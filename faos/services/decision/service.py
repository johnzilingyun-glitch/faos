import logging
from faos.services.decision.models import (
    DecisionRequest, DecisionResult, PMDecision, PM_DECISION_JSON_HINT,
)
from faos.services.decision.prompts import TRADER_PROMPT, PORTFOLIO_MANAGER_PROMPT
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.services.decision.policy_engine import PolicyEngine
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
        self.policy_engine = PolicyEngine()
        logger.info("DecisionService initialized with Trader and Portfolio Manager roles")

    async def evaluate(self, request: DecisionRequest) -> DecisionResult:
        logger.info(f"DecisionService evaluating Task {request.task_id}")
        
        # Parse full context
        user_params = request.reasoning_results.get("user_parameters", {})
        provider_outputs = request.context_data.get("provider_outputs", {})
        
        symbol = (
            user_params.get("symbol")
            or provider_outputs.get("quote", {}).get("symbol")
            or "Asset"
        )
        
        discussion = request.reasoning_results.get("discussion", {})
        if isinstance(discussion, dict):
            # DiscussSkill stores {'Investment Plan': ..., 'Risk Plan': ...}; older
            # callers may pass {'consensus': ...}. Support both.
            discussion_consensus = discussion.get("consensus", "")
            if not discussion_consensus:
                parts = []
                if discussion.get("Investment Plan"):
                    parts.append(f"--- Investment Plan ---\n{discussion['Investment Plan']}")
                if discussion.get("Risk Plan"):
                    parts.append(f"--- Risk Plan ---\n{discussion['Risk Plan']}")
                discussion_consensus = "\n\n".join(parts)
        else:
            discussion_consensus = str(discussion)
        analysis_reports = request.reasoning_results.get("analysis_reports", {})
        
        evidence = request.context_data.get("evidence", [])
        if not evidence:
            if discussion_consensus:
                evidence = ["Analyzed multi-agent discussion consensus."]
            elif analysis_reports:
                evidence = ["Analyzed multi-dimensional research reports."]
            else:
                evidence = [f"Analyzed market data and news for {symbol}."]

        trader_context = {
            "symbol": symbol,
            "user_parameters": user_params,
            "analysis_reports": analysis_reports,
            "discussion_consensus": discussion_consensus,
            "provider_outputs": provider_outputs
        }
        
        # Step 1: Trader generates proposal
        trader_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=trader_context,
            prompt=TRADER_PROMPT,
            llm_config=request.llm_config
        )
        trader_resp = await self.reasoning.analyze_context(trader_req)
        trader_proposal = trader_resp.raw_response
        
        # Step 2: Portfolio Manager makes final decision (STRUCTURED — no regex)
        pm_context = {
            "symbol": symbol,
            "user_parameters": user_params,
            "analysis_reports": analysis_reports,
            "discussion_consensus": discussion_consensus,
            "trader_proposal": trader_proposal,
            "provider_outputs": provider_outputs
        }
        pm_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=pm_context,
            prompt=PORTFOLIO_MANAGER_PROMPT,
            llm_config=request.llm_config
        )
        pm, pm_raw = await self.reasoning.analyze_structured(
            pm_req, PMDecision, PM_DECISION_JSON_HINT
        )
        if pm is None:
            # Degrade gracefully: fall back to legacy text parsing of the raw output.
            pm = self._parse_pm_text(pm_raw)
        
        action = pm.action.upper() if pm.action.upper() in ("BUY", "SELL", "HOLD") else "HOLD"
        confidence = pm.confidence
        risk_score = pm.risk_score
        reason = pm.rationale or pm_raw
            
        # Calculate unified score
        score = self.policy_engine.calculate_unified_score(
            evidence=evidence, 
            sentiment=0.5, 
            confidence=confidence
        )
            
        # Create tentative decision
        decision = DecisionResult(
            action=action,
            score=score,
            confidence=confidence,
            risk=risk_score,
            reason=reason,
            strategy=trader_proposal,
            evidence=evidence,
            scorecard=pm.scorecard.model_dump()
        )
        
        # Step 3: Run Policy Engine Guardrails
        final_decision = self.policy_engine.evaluate_guardrails(decision, request.policy)
        
        return final_decision

    def _parse_pm_text(self, pm_decision: str) -> PMDecision:
        """Legacy fallback: extract a PMDecision from free text (structured parse failed)."""
        action = "HOLD"
        if re.search(r'\bBUY\b', pm_decision, re.IGNORECASE) or "买入" in pm_decision or "做多" in pm_decision:
            action = "BUY"
        elif re.search(r'\bSELL\b', pm_decision, re.IGNORECASE) or "卖出" in pm_decision or "做空" in pm_decision:
            action = "SELL"
        
        confidence = 0.8
        conf_match = re.search(r'(?:confidence|置信度|信心)[^\d]*(\d+(?:\.\d+)?)', pm_decision, re.IGNORECASE)
        if conf_match:
            try:
                val = float(conf_match.group(1))
                confidence = val if val <= 1.0 else val / 100.0
            except ValueError:
                pass
        
        risk_score = 50
        if "high risk" in pm_decision.lower() or "高风险" in pm_decision:
            risk_score = 85
        elif "low risk" in pm_decision.lower() or "低风险" in pm_decision:
            risk_score = 20
        
        return PMDecision(
            action=action, confidence=confidence,
            risk_score=risk_score, rationale=pm_decision,
        )
