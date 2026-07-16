from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from faos.core.context import ExecutionContext

class SkillRequest(BaseModel):
    task_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # We use model_config to allow arbitrary types for ExecutionContext
    model_config = {"arbitrary_types_allowed": True}
    context: ExecutionContext

class SkillResponse(BaseModel):
    status: str = Field(..., description="Status of the skill execution, e.g., 'success', 'failed'")
    output: Dict[str, Any] = Field(default_factory=dict, description="Output data from the skill")
    error: Optional[str] = Field(None, description="Error message if failed")

class SkillManifest(BaseModel):
    id: str
    name: str
    capability: str
    version: str = "1.0"
    description: str = ""
