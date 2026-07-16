import uuid
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class DecisionPolicy(BaseModel):
    name: str = "Standard"
    max_risk_tolerance: int = Field(80, description="Maximum allowed risk score (0-100)")
    min_confidence_required: float = Field(0.5, description="Minimum confidence required (0.0-1.0)")
    allowed_assets: List[str] = Field(default_factory=lambda: ["STOCK", "ETF"])
    require_consensus: bool = True

class DecisionRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict)
    reasoning_results: Dict[str, Any] = Field(default_factory=dict)
    policy: DecisionPolicy = Field(default_factory=DecisionPolicy)
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="Dynamic LLM configuration")

class DecisionResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "InvestmentDecision"
    action: str = Field(..., description="Action to take, e.g., BUY, SELL, HOLD, REJECT, REVIEW")
    score: int = Field(..., description="Standardized score from 0 to 100")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    risk: int = Field(..., description="Evaluated risk score from 0 to 100")
    strategy: Optional[str] = None
    allocation: Optional[Dict[str, float]] = Field(default_factory=dict)
    reason: str = Field(..., description="Reason for the decision")
    evidence: List[str] = Field(default_factory=list, description="List of supporting evidence")
