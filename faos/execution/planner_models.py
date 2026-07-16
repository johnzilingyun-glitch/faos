from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class PlannerResponse(BaseModel):
    workflow_id: str = Field(description="The ID of the selected workflow that best matches the user intent.")
    parameters: Dict[str, Any] = Field(description="Extracted parameters (e.g. 'symbol') required for the workflow.", default_factory=dict)
    reasoning: Optional[str] = Field(description="The reasoning behind selecting this workflow and parameters.", default=None)
