import os
import logging
from typing import Optional
import pyexasol
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from investigation.engine import InvestigationEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Helpers ---
def get_exasol_connection():
    """Utility to establish a connection with Exasol SaaS and open MAIN schema."""
    conn = pyexasol.connect(
        dsn=os.getenv("EXASOL_HOST"),
        user=os.getenv("EXASOL_USER"),
        password=os.getenv("EXASOL_PASSWORD"),
        autocommit=True
    )
    conn.execute("OPEN SCHEMA MAIN;")
    return conn

# --- Pydantic Schemas ---
class InvestigateRequest(BaseModel):
    query: str

class ChallengeRequest(BaseModel):
    context: Optional[str] = None

# --- Dependency Injection Helpers ---
def get_investigation_engine() -> InvestigationEngine:
    return InvestigationEngine()

# --- Endpoints ---

@router.get("/health", summary="Health Check")
async def health_check():
    return {"status": "ok"}

@router.get("/db-test", summary="Exasol DB Health Check")
async def db_test():
    try:
        conn = get_exasol_connection()
        res = conn.execute("SELECT 1 AS status;").fetchall()
        conn.close()
        return {"status": "connected", "result": res}
    except Exception as e:
        logger.error(f"Exasol connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.post("/investigate", summary="Run Investigation")
async def run_investigation(
    payload: InvestigateRequest,
    engine: InvestigationEngine = Depends(get_investigation_engine)
):
    try:
        logger.info(f"Received investigation request for prompt: '{payload.query}'")
        result = await engine.run_investigation(payload.query)
        return result
    except Exception as e:
        logger.error(f"Error during investigation execution: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.post("/investigate/{investigation_id}/challenge", summary="Challenge Investigation")
async def challenge_investigation(
    investigation_id: str,
    payload: Optional[ChallengeRequest] = None,
    engine: InvestigationEngine = Depends(get_investigation_engine)
):
    try:
        logger.info(f"Running challenge workflow for investigation_id: {investigation_id}")
        updated_result = await engine.run_challenge_workflow(investigation_id)
        
        return {
            "investigation_id": investigation_id,
            "challengedScore": updated_result.get("challengedScore", 42),
            "counterEvidence": updated_result.get("counterEvidence", "Counter-analysis reveals localized baseline trends.")
        }
    except Exception as e:
        logger.error(f"Error during challenge workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Challenge workflow failed: {str(e)}")

@router.get("/schema", summary="Get Database Schema")
async def get_schema():
    """
    Retrieves column structure by querying EXA_ALL_COLUMNS for table_schema = 'MAIN'.
    """
    try:
        conn = get_exasol_connection()
        sql = """
            SELECT column_table, column_name, column_type
            FROM EXA_ALL_COLUMNS
            WHERE column_schema = 'MAIN'
            ORDER BY column_table, column_ordinal_position;
        """
        rows = conn.execute(sql).fetchall()
        conn.close()

        tables_dict = {}
        for table_name, col_name, col_type in rows:
            if table_name not in tables_dict:
                tables_dict[table_name] = []
            tables_dict[table_name].append({"name": col_name, "type": col_type})

        tables = [{"table_name": k, "columns": v} for k, v in tables_dict.items()]
        return {"tables": tables}
        
    except Exception as e:
        logger.error(f"Error fetching Exasol schema: {str(e)}")
        return {"tables": []}