from pydantic import BaseModel, Field
from typing import List, Dict, Any

class WorkflowNodeDef(BaseModel):
    id: str
    capability: str
    dependencies: List[str] = Field(default_factory=list)

class WorkflowDefinition(BaseModel):
    id: str
    name: str
    description: str = ""
    nodes: List[WorkflowNodeDef] = Field(default_factory=list)
