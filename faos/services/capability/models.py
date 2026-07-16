from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class CapabilityManifest(BaseModel):
    id: str
    name: str
    description: str = ""
    domain: List[str] = Field(default_factory=list)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    requires: List[str] = Field(default_factory=list)
    default_workflow: Optional[str] = None
    policies: Dict[str, Any] = Field(default_factory=dict)
    reasoning: bool = False
    providers: List[str] = Field(default_factory=list)
