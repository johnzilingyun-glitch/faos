import logging
import asyncio
from faos.services.decision.models import DecisionRequest, DecisionResult

logger = logging.getLogger(__name__)

class DecisionService:
    """
    Decision Service is the central decision-making hub.
    It applies policies and strategies to reasoning results to produce final actionable decisions.
    """
    def __init__(self):
        logger.info("DecisionService initialized")

    async def evaluate(self, request: DecisionRequest) -> DecisionResult:
        logger.info(f"DecisionService evaluating Task {request.task_id} with policy {request.policy}")
        await asyncio.sleep(0.5)
        
        # Simple Mock Rule Engine
        reasoning = request.reasoning_results
        
        # Extract sentiment from reasoning
        sentiment = reasoning.get("sentiment", 0.5)
        
        action = "HOLD"
        confidence = 0.5
        reason = "Neutral signals"
        
        if sentiment > 0.6:
            action = "BUY"
            confidence = 0.8
            reason = "Positive sentiment and strong reasoning indicators"
        elif sentiment < 0.4:
            action = "SELL"
            confidence = 0.8
            reason = "Negative sentiment and weak reasoning indicators"
            
        return DecisionResult(
            action=action,
            confidence=confidence,
            reason=reason,
            risk="Medium",
            strategy="Trend Following"
        )
