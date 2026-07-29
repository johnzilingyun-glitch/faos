from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
import uuid

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    
class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent: str
    status: str = "created"
    context: Dict[str, Any] = Field(default_factory=dict)

class PlanNode(BaseModel):
    id: str
    capability: str
    dependencies: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
class ExecutionPlan(BaseModel):
    task_id: str
    nodes: List[PlanNode] = Field(default_factory=list)
