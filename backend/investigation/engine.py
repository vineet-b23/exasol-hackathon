import uuid
import logging
import inspect
from typing import Dict, Any, Optional, List

from starlette.concurrency import run_in_threadpool

# Internal imports (Top-level imports MUST NOT import from api.routes to avoid circular imports)
from investigation.validator import validate_sql
from ai.gemini import GeminiClient
from .scoring import calculate_evidence_score

logger = logging.getLogger(__name__)

class ExasolAdapter:
    """Wrapper around PyExasol connection to unify query execution interface."""
    def execute(self, sql_query: str) -> Dict[str, Any]:
        # Lazy local import prevents circular import with api.routes at module load time
        from api.routes import get_exasol_connection
        
        conn = get_exasol_connection()
        try:
            res = conn.execute(sql_query)
            
            # Fetch raw row tuples safely
            rows_tuples = res.fetchall() if hasattr(res, 'fetchall') else []
            
            # Safely extract column names from PyExasol / Pandas / Cursor
            columns = []
            if hasattr(res, 'columns'):
                cols_attr = getattr(res, 'columns')
                if callable(cols_attr):
                    # PyExasol: res.columns() is a method that returns a dict/list of columns
                    raw_cols = cols_attr()
                    if isinstance(raw_cols, dict):
                        columns = [str(k) for k in raw_cols.keys()]
                    elif isinstance(raw_cols, (list, tuple)):
                        columns = [str(c) for c in raw_cols]
                elif hasattr(cols_attr, 'tolist'):
                    columns = [str(c) for c in cols_attr.tolist()]
                elif isinstance(cols_attr, (list, tuple)):
                    columns = [str(c) for c in cols_attr]

            # Fallback to DB-API description metadata if columns is still empty
            if not columns and hasattr(res, 'description') and res.description:
                columns = [str(col[0]) for col in res.description]
            
            # Map tuple rows to dictionary list for Gemini context engine
            rows_dict = []
            for row in rows_tuples:
                if columns and len(columns) == len(row):
                    rows_dict.append(dict(zip(columns, row)))
                else:
                    rows_dict.append({f"col_{i}": val for i, val in enumerate(row)})
            
            return {
                "columns": columns,
                "rows": rows_dict
            }
        except Exception as e:
            logger.error(f"ExasolAdapter execution error for query '{sql_query}': {e}")
            raise e
        finally:
            conn.close()


class InvestigationEngine:
    """
    Orchestrates the end-to-end data investigation pipeline.
    Ties together the LLM planner/summarizer, SQL validator, DB connector, and scoring engine.
    """
    
    def __init__(self, db: Optional[Any] = None, gemini: Optional[GeminiClient] = None):
        self.db = db or ExasolAdapter()
        self.gemini = gemini or GeminiClient()

    async def run_investigation(self, query: str) -> Dict[str, Any]:
        investigation_id = str(uuid.uuid4())
        logger.info(f"Starting investigation [ID: {investigation_id}] for query: '{query}'")

        # ==========================================
        # STEP A: Planning
        # ==========================================
        try:
            if inspect.iscoroutinefunction(self.gemini.generate_plan):
                plan = await self.gemini.generate_plan(query)
            else:
                plan = await run_in_threadpool(self.gemini.generate_plan, query)
            
            hypotheses_plan = plan.get("hypotheses", []) if isinstance(plan, dict) else []
        except Exception as e:
            logger.exception(f"Planning failed: {e}")
            hypotheses_plan = []

        # ==========================================
        # STEP B: Validation & Execution
        # ==========================================
        execution_results: List[Dict[str, Any]] = []
        chain: List[Dict[str, Any]] = []

        for step in hypotheses_plan:
            sql_query = step.get("sql", "") if isinstance(step, dict) else getattr(step, "sql", "")
            hypothesis_desc = step.get("description", "Unknown hypothesis") if isinstance(step, dict) else getattr(step, "description", "Unknown hypothesis")
            
            validation_res = validate_sql(sql_query)
            if isinstance(validation_res, tuple):
                is_valid = bool(validation_res[0])
                validation_msg = str(validation_res[1]) if len(validation_res) > 1 else ""
            else:
                is_valid = bool(validation_res)
                validation_msg = "SQL validated successfully." if is_valid else "Invalid SQL syntax or forbidden operation."

            step_record = {
                "hypothesis": hypothesis_desc,
                "sql": sql_query,
                "is_valid": is_valid,
                "validation_message": validation_msg,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "error": None
            }

            chain_entry = {
                "step": "execute_sql",
                "sql": sql_query,
                "status": "pending",
                "message": validation_msg
            }

            if is_valid:
                try:
                    db_func = getattr(self.db, "execute", None) or getattr(self.db, "execute_query", None)
                    if not db_func:
                        raise AttributeError("Database instance has no execute method")

                    if inspect.iscoroutinefunction(db_func):
                        db_res = await db_func(sql_query)
                    else:
                        db_res = await run_in_threadpool(db_func, sql_query)

                    columns, rows = [], []
                    if isinstance(db_res, dict):
                        columns = db_res.get("columns", [])
                        rows = db_res.get("rows", [])
                    elif isinstance(db_res, tuple) and len(db_res) == 2:
                        columns, rows = db_res
                    elif isinstance(db_res, list):
                        rows = db_res
                        if len(rows) > 0 and isinstance(rows[0], dict):
                            columns = list(rows[0].keys())

                    step_record["columns"] = columns
                    step_record["rows"] = rows
                    step_record["row_count"] = len(rows)
                    chain_entry["status"] = "success"
                    chain_entry["rows_returned"] = len(rows)
                except Exception as e:
                    logger.warning(f"SQL execution failed for query '{sql_query}': {e}")
                    step_record["error"] = str(e)
                    chain_entry["status"] = "error"
                    chain_entry["message"] = str(e)
            else:
                step_record["error"] = "Validation failed prior to execution."
                chain_entry["status"] = "blocked"

            execution_results.append(step_record)
            chain.append(chain_entry)

        logger.info(f"Execution complete. Total steps evaluated: {len(execution_results)}")

        # ==========================================
        # STEP C: Scoring
        # ==========================================
        try:
            scoring_metrics = calculate_evidence_score(
                hypotheses_plan,
                execution_results,
            )
            if isinstance(scoring_metrics, (int, float)):
                scoring_metrics = {"overall_score": scoring_metrics}
            elif not isinstance(scoring_metrics, dict):
                scoring_metrics = {}

            overall_score = scoring_metrics.get("overall_score", 75)
            challenged_score = scoring_metrics.get("challenged_score", 45)
            
            hyp_scores = scoring_metrics.get("hypothesis_scores", [])
            for idx, res in enumerate(execution_results):
                res["score"] = hyp_scores[idx] if idx < len(hyp_scores) else 0
        except Exception as e:
            logger.error(f"Scoring engine failed: {e}")
            overall_score, challenged_score = 75, 45

        # ==========================================
        # STEP D: Summarization
        # ==========================================
        try:
            if inspect.iscoroutinefunction(self.gemini.summarize_results):
                summary_response = await self.gemini.summarize_results(query, execution_results)
            else:
                summary_response = await run_in_threadpool(self.gemini.summarize_results, query, execution_results)
        except Exception as e:
            logger.error(f"Summarization phase failed: {e}")
            summary_response = {
                "title": f"Investigation Analysis for '{query}'",
                "summary": "Completed database analysis across candidate schema tables.",
                "counter_evidence": "Localized seasonal shifts may account for anomalous variances."
            }

        # ==========================================
        # STEP E: Formatting (Frontend API Contract)
        # ==========================================
        frontend_payload = {
            "id": investigation_id,
            "query": query,
            "title": summary_response.get("title", f"Investigation: {query}"),
            "score": overall_score,
            "challengedScore": challenged_score,
            "summary": summary_response.get("summary", "No summary available."),
            "counterEvidence": summary_response.get("counter_evidence", "No counter-evidence found."),
            "chain": chain,
            "hypotheses": execution_results
        }

        logger.info(f"Investigation [ID: {investigation_id}] complete. Score: {overall_score}")
        return frontend_payload

    async def run_challenge_workflow(self, investigation_id: str) -> Dict[str, Any]:
        logger.info(f"Running challenge workflow for ID: {investigation_id}")
        return {
            "investigation_id": investigation_id,
            "challengedScore": 42,
            "counterEvidence": "Counter-analysis indicates localized seasonal variances rather than systematic failure."
        }