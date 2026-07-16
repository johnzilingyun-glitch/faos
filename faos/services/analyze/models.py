from pydantic import BaseModel, Field
from typing import Dict, Any

class AnalyzeRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Raw data from providers")

class AnalyzeResponse(BaseModel):
    task_id: str
    status: str
    analyst_reports: Dict[str, str] = Field(default_factory=dict, description="Reports from the 4 analysts")
    error: str = None
