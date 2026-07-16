from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ReportRequest(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="All data needed for the report")
    format: str = Field(default="markdown", description="Requested format: markdown, json, etc.")
    
class ReportResponse(BaseModel):
    format: str = Field(..., description="The format of the returned content")
    content: Any = Field(..., description="The generated report content")
    status: str = Field(default="success")
    error: Optional[str] = None
