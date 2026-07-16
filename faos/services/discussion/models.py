from pydantic import BaseModel, Field
from typing import Dict, Any, List

class AgentOpinion(BaseModel):
    name: str = Field(..., description="Name of the agent (e.g., Fundamental Analyst)")
    role: str = Field(..., description="Role of the agent")
    opinion: str = Field(..., description="The textual opinion of the agent")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")

class DiscussionRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict, description="The data to discuss")

class DiscussionResponse(BaseModel):
    status: str = Field(..., description="Status of the discussion, 'success' or 'failed'")
    consensus: str = Field(default="", description="The synthesized final consensus")
    opinions: List[AgentOpinion] = Field(default_factory=list, description="The individual agent opinions")
    error: str = Field(default="")
