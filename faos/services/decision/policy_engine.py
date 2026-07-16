import logging
from typing import Dict, Any

from faos.services.decision.models import DecisionPolicy, DecisionResult

logger = logging.getLogger(__name__)


class PolicyEngine:
    """
    Enforces rules and guardrails for decisions before they are finalized.
    This fulfills the requirement in Chapter 14.25 (Guardrails).
    """
    
    def __init__(self, default_policy: DecisionPolicy = None):
        self.default_policy = default_policy or DecisionPolicy()
        
    def evaluate_guardrails(self, decision: DecisionResult, policy: DecisionPolicy = None) -> DecisionResult:
        """
        Evaluate hard rules on the proposed decision.
        If a rule is violated, the decision's action will be forcefully overridden to REJECT.
        """
        active_policy = policy or self.default_policy
        
        logger.info(f"PolicyEngine evaluating decision {decision.id} against policy '{active_policy.name}'")
        
        # Guardrail 1: Risk Tolerance
        if decision.risk > active_policy.max_risk_tolerance:
            logger.warning(f"Guardrail violation: Risk ({decision.risk}) exceeds maximum ({active_policy.max_risk_tolerance})")
            decision.action = "REJECT"
            decision.reason += f"\n[GUARDRAIL REJECT]: Risk exceeds policy maximum."
            return decision
            
        # Guardrail 2: Minimum Confidence
        if decision.confidence < active_policy.min_confidence_required:
            logger.warning(f"Guardrail violation: Confidence ({decision.confidence}) below minimum ({active_policy.min_confidence_required})")
            decision.action = "REVIEW"
            decision.reason += f"\n[GUARDRAIL REVIEW]: Confidence is too low."
            return decision
            
        # Guardrail 3: Evidence Requirement (Chapter 14.12)
        if not decision.evidence or len(decision.evidence) == 0:
            logger.warning(f"Guardrail violation: No evidence provided.")
            decision.action = "REJECT"
            decision.reason += f"\n[GUARDRAIL REJECT]: Decision requires evidence."
            return decision

        logger.info("PolicyEngine guardrails passed.")
        return decision

    def calculate_unified_score(self, evidence: list, sentiment: float, confidence: float) -> int:
        """
        Calculate a unified 0-100 score based on Evidence, Consensus, and Confidence.
        """
        score = 50  # Base neutral score
        
        # Add points for evidence length (up to 20)
        evidence_points = min(len(evidence) * 5, 20)
        score += evidence_points
        
        # Adjust by sentiment (-20 to +20)
        sentiment_adj = (sentiment - 0.5) * 40
        score += sentiment_adj
        
        # Adjust by confidence
        if confidence > 0.8:
            score += 10
        elif confidence < 0.4:
            score -= 10
            
        return max(0, min(100, int(score)))
