from pydantic import BaseModel, Field
from typing import Dict, Any
from faos.services.reasoning.schemas import AnalystReport

class AnalyzeRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Raw data from providers")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="Dynamic LLM configuration")

class AnalyzeResponse(BaseModel):
    task_id: str
    status: str
    analyst_reports: Dict[str, str] = Field(default_factory=dict, description="Rendered markdown reports (back-compat)")
    structured_reports: Dict[str, AnalystReport] = Field(default_factory=dict, description="Structured analyst reports (facts/evidence/signals/inferences)")
    error: str = None
