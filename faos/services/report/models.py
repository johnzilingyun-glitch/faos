from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import datetime

class ReportSection(BaseModel):
    title: str
    content: str
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)

class Report(BaseModel):
    title: str = "FAOS Analysis Report"
    summary: str = ""
    sections: List[ReportSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: str = Field(default_factory=lambda: datetime.datetime.utcnow().isoformat())

class ReportRequest(BaseModel):
    task_id: str = Field(..., description="ID of the task")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="All data needed for the report")
    format: str = Field(default="markdown", description="Requested format: markdown, json, etc.")
    
class ReportResponse(BaseModel):
    format: str = Field(..., description="The format of the returned content")
    content: Any = Field(..., description="The generated report content")
    status: str = Field(default="success")
    error: Optional[str] = None
