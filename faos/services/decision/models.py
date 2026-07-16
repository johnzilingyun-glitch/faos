from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class DecisionRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    reasoning_results: Dict[str, Any] = Field(default_factory=dict)
    policy: str = "Standard"

class DecisionResult(BaseModel):
    action: str = Field(..., description="Action to take, e.g., BUY, SELL, HOLD")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    reason: str = Field(..., description="Reason for the decision")
    risk: Optional[str] = None
    strategy: Optional[str] = None
