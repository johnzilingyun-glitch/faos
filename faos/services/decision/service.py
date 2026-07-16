import logging
from faos.services.decision.models import DecisionRequest, DecisionResult
from faos.services.decision.prompts import TRADER_PROMPT, PORTFOLIO_MANAGER_PROMPT
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
import re

logger = logging.getLogger(__name__)

class DecisionService:
    """
    Decision Service acts as the Trader and Portfolio Manager.
    It takes the Discussion Service output (Investment Plan + Risk Plan)
    and formulates a strategy and makes a final decision.
    """
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning = reasoning_service
        logger.info("DecisionService initialized with Trader and Portfolio Manager roles")

    async def evaluate(self, request: DecisionRequest) -> DecisionResult:
        logger.info(f"DecisionService evaluating Task {request.task_id}")
        
        # In this workflow, reasoning_results should contain the 'discussion' output
        # which has the consensus string (Investment Plan + Risk Plan)
        discussion_consensus = request.reasoning_results.get("discussion", {}).get("consensus", "")
        
        # Step 1: Trader generates proposal
        trader_req = ReasoningRequest(
            task_id=request.task_id,
            context_data={"consensus": discussion_consensus},
            prompt=TRADER_PROMPT,
            llm_config=request.llm_config
        )
        trader_resp = await self.reasoning.analyze_context(trader_req)
        trader_proposal = trader_resp.raw_response
        
        # Step 2: Portfolio Manager makes final decision
        pm_context = {
            "consensus": discussion_consensus,
            "trader_proposal": trader_proposal
        }
        pm_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=pm_context,
            prompt=PORTFOLIO_MANAGER_PROMPT,
            llm_config=request.llm_config
        )
        pm_resp = await self.reasoning.analyze_context(pm_req)
        pm_decision = pm_resp.raw_response
        
        # Parse output for BUY/HOLD/SELL
        action = "HOLD"
        if re.search(r'\bBUY\b', pm_decision, re.IGNORECASE):
            action = "BUY"
        elif re.search(r'\bSELL\b', pm_decision, re.IGNORECASE):
            action = "SELL"
            
        return DecisionResult(
            action=action,
            confidence=pm_resp.confidence,
            reason=pm_decision,
            risk="Analyzed by Risk Plan",
            strategy=trader_proposal
        )
