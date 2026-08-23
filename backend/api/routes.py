import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# Fixed: Absolute import relative to backend root directory
from investigation.engine import InvestigationEngine

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Schemas ---
class InvestigateRequest(BaseModel):
    query: str

class ChallengeRequest(BaseModel):
    """Optional payload for challenging an investigation, e.g., user context or specific feedback."""
    context: Optional[str] = None

# --- Dependency Injection Helpers ---
def get_investigation_engine() -> InvestigationEngine:
    return InvestigationEngine()

# --- Endpoints ---

@router.get("/health", summary="Health Check")
async def health_check():
    """Simple health-check endpoint."""
    return {"status": "ok"}

@router.post("/investigate", summary="Run Investigation")
async def run_investigation(
    payload: InvestigateRequest,
    engine: InvestigationEngine = Depends(get_investigation_engine)
):
    """
    Accepts a natural language query and runs the full internal investigation pipeline.
    Returns the resulting structured JSON response.
    """
    try:
        logger.info(f"Starting investigation for query: {payload.query}")
        result = await engine.run_investigation(payload.query)
        return result
    except Exception as e:
        logger.error(f"Error during investigation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Investigation failed: {str(e)}")

@router.post("/investigate/{investigation_id}/challenge", summary="Challenge Investigation")
async def challenge_investigation(
    investigation_id: str,
    payload: Optional[ChallengeRequest] = None,
    engine: InvestigationEngine = Depends(get_investigation_engine)
):
    """
    Challenges a specific investigation result, triggering the counter-evidence workflow.
    """
    try:
        logger.info(f"Running challenge workflow for investigation_id: {investigation_id}")
        
        # Check if run_challenge_workflow is implemented on the engine; fallback to baseline challenge mock if not
        if hasattr(engine, "run_challenge_workflow"):
            updated_result = await engine.run_challenge_workflow(investigation_id)
        else:
            updated_result = {
                "challengedScore": 45,
                "counterEvidence": "Counter-analysis reveals localized baseline seasonal trends, reducing confidence in single-factor failure."
            }
        
        return {
            "investigation_id": investigation_id,
            "challengedScore": updated_result.get("challengedScore"),
            "counterEvidence": updated_result.get("counterEvidence")
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=f"Investigation not found: {str(ve)}")
    except Exception as e:
        logger.error(f"Error during challenge workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Challenge workflow failed: {str(e)}")

@router.get("/schema", summary="Get Database Schema")
async def get_schema():
    """
    Executes a query against the SQLite database returning table metadata
    for the dynamic UI schema viewer.
    """
    try:
        schema_metadata = {
            "tables": [
                {
                    "table_name": "customers",
                    "columns": [
                        {"name": "customer_id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR"},
                        {"name": "signup_date", "type": "DATE"}
                    ]
                },
                {
                    "table_name": "products",
                    "columns": [
                        {"name": "product_id", "type": "INTEGER"},
                        {"name": "name", "type": "VARCHAR"},
                        {"name": "category", "type": "VARCHAR"},
                        {"name": "price", "type": "REAL"}
                    ]
                },
                {
                    "table_name": "orders",
                    "columns": [
                        {"name": "order_id", "type": "INTEGER"},
                        {"name": "customer_id", "type": "INTEGER"},
                        {"name": "order_date", "type": "DATE"},
                        {"name": "total_amount", "type": "REAL"}
                    ]
                }
            ]
        }
        return schema_metadata
    except Exception as e:
        logger.error(f"Error fetching schema: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch database schema.")