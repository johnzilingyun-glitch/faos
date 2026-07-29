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
    scorecard: Optional[Dict[str, Any]] = Field(default=None, description="Final decision scorecard (investment_score / risk_level / catalyst / valuation / macro / recommendation)")


# ── Structured decision schemas (Phase 3: scorecard) ─────────────────────

class Scorecard(BaseModel):
    """Compact final decision card (the answer to 'so what should I do?')."""
    investment_score: int = Field(default=50, ge=0, le=100)
    risk_level: str = Field(default="medium", description="'low' | 'medium' | 'high'")
    catalyst: int = Field(default=3, ge=1, le=5, description="Catalyst strength, 1-5 stars")
    valuation: int = Field(default=3, ge=1, le=5, description="Valuation attractiveness, 1-5 stars")
    macro: int = Field(default=3, ge=1, le=5, description="Macro tailwind, 1-5 stars")
    recommendation: str = Field(default="Watch", description="e.g. Buy / Watch / Hold / Reduce / Avoid")

    def render(self, lang: str = "zh") -> str:
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        stars = lambda n: "★" * int(n) + "☆" * (5 - int(n))
        risk_map = {"low": "低" if zh else "Low", "medium": "中" if zh else "Medium", "high": "高" if zh else "High"}
        risk = risk_map.get(self.risk_level, self.risk_level)
        rows = [
            ("投资评分" if zh else "Investment Score", str(self.investment_score)),
            ("风险等级" if zh else "Risk", risk),
            ("催化剂" if zh else "Catalyst", stars(self.catalyst)),
            ("估值" if zh else "Valuation", stars(self.valuation)),
            ("宏观" if zh else "Macro", stars(self.macro)),
            ("操作建议" if zh else "Recommendation", f"**{self.recommendation}**"),
        ]
        header = "| " + ("维度" if zh else "Dimension") + " | " + ("评定" if zh else "Rating") + " |"
        lines = [header, "| --- | --- |"]
        lines += [f"| {k} | {v} |" for k, v in rows]
        return "\n".join(lines)


class PMDecision(BaseModel):
    """Structured Portfolio Manager output — replaces regex extraction."""
    action: str = Field(default="HOLD", description="'BUY' | 'HOLD' | 'SELL'")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    risk_score: int = Field(default=50, ge=0, le=100)
    rationale: str = Field(default="")
    scorecard: Scorecard = Field(default_factory=Scorecard)


PM_DECISION_JSON_HINT = (
    '{\n'
    '  "action": "BUY|HOLD|SELL",\n'
    '  "confidence": 0.0-1.0,\n'
    '  "risk_score": 0-100,\n'
    '  "rationale": str,\n'
    '  "scorecard": {"investment_score": 0-100, "risk_level": "low|medium|high", '
    '"catalyst": 1-5, "valuation": 1-5, "macro": 1-5, "recommendation": "Buy|Watch|Hold|Reduce|Avoid"}\n'
    '}'
)
