from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PlannerResponse(BaseModel):
    status: str = Field(description="'clarify' if more info is needed, 'ready' if parameters are fully extracted.")
    message: Optional[str] = Field(description="Question to ask the user if status is 'clarify'.", default=None)
    workflow_id: Optional[str] = Field(description="The ID of the selected workflow that best matches the user intent.", default=None)
    parameters: Dict[str, Any] = Field(description="Extracted parameters (e.g. 'symbol') required for the workflow.", default_factory=dict)
    reasoning: Optional[str] = Field(description="The reasoning behind selecting this workflow and parameters.", default=None)
