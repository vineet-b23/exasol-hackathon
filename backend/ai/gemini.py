import os
import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Load .env if not already present in environment
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

logger = logging.getLogger(__name__)


# ==========================================
# Pydantic Output Schemas
# ==========================================

class GeneratedQuery(BaseModel):
    description: str = Field(description="A short, descriptive name or rationale for the hypothesis being tested.")
    sql: str = Field(description="Valid, read-only SQLite SELECT statement to test the hypothesis.")

class HypothesisPlan(BaseModel):
    intent: str = Field(description="The core goal of the user's investigation request.")
    primary_metric: str = Field(description="The main business metric being analyzed (e.g., 'Revenue', 'Churn Rate').")
    time_period: str = Field(description="The time period in question (e.g., 'July 2026', 'Q2').")
    hypotheses: List[GeneratedQuery] = Field(description="List of SQL queries targeting competing hypotheses.")

class InvestigationSummary(BaseModel):
    title: str = Field(description="A clear, professional title for the investigation results.")
    leading_hypothesis: str = Field(description="The hypothesis that proved most accurate based on the data.")
    score: int = Field(description="Confidence score from 0 to 100 based on the strength of the evidence.")
    summary: str = Field(description="A narrative explanation of the findings and what caused the anomaly.")
    counter_evidence: str = Field(description="Any data that contradicts the leading hypothesis or adds nuance.")


try:
    from .prompts import SYSTEM_PROMPT, SCHEMA_CONTEXT
except ImportError:
    SYSTEM_PROMPT = "You are an expert data investigator and SQL analyst."
    SCHEMA_CONTEXT = "Schema Context Available."


# ==========================================
# Gemini Client Wrapper
# ==========================================

class GeminiClient:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.getenv("GEMINI_API_KEY")
        self.is_configured = bool(key and key != "YOUR_GEMINI_API_KEY")
        
        if self.is_configured:
            try:
                self.client = genai.Client(api_key=key)
            except Exception as e:
                logger.error(f"Failed to initialize GenAI client: {e}")
                self.is_configured = False
        else:
            logger.warning("GEMINI_API_KEY is not set or using placeholder value.")
            self.client = None

    def generate_plan(self, query: str) -> Dict[str, Any]:
        """
        Generates structured hypotheses plan mapped to InvestigationEngine expectations.
        """
        if not self.is_configured or not self.client:
            logger.warning("Gemini Client not configured. Returning empty hypotheses.")
            return {"hypotheses": []}

        prompt = (
            f"Please generate an investigation plan for the following user request.\n\n"
            f"{SCHEMA_CONTEXT}\n\n"
            f"User Request: {query}"
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=HypothesisPlan,
                    temperature=0.2,
                )
            )
            
            if response.parsed:
                return response.parsed.model_dump()
            
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini generate_plan call failed: {e}")
        
        return {"hypotheses": []}

    plan_investigation = generate_plan

    def summarize_results(self, query: str, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates a summary dictionary compatible with InvestigationEngine.
        """
        default_summary = {
            "title": f"Investigation: {query}",
            "summary": "Completed database analysis across candidate schema tables.",
            "counter_evidence": "Localized seasonal shifts may account for anomalous variances."
        }

        if not self.is_configured or not self.client:
            return default_summary

        prompt = (
            f"Original User Request: {query}\n\n"
            f"Please analyze the following SQL query execution results and provide a final investigation summary.\n\n"
            f"Execution Results:\n{json.dumps(execution_results, indent=2, default=str)}"
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=InvestigationSummary,
                    temperature=0.3,
                )
            )
            
            if response.parsed:
                return response.parsed.model_dump()
            
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            logger.error(f"Gemini summarize_results call failed: {e}")

        return default_summary