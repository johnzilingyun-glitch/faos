import asyncio
import logging
from typing import List

from faos.services.discussion.models import DiscussionRequest, DiscussionResponse, AgentOpinion
from faos.services.discussion.prompts import (
    BULL_RESEARCHER_PROMPT,
    BEAR_RESEARCHER_PROMPT,
    RESEARCH_MANAGER_PROMPT,
    AGGRESSIVE_RISK_PROMPT,
    CONSERVATIVE_RISK_PROMPT,
    NEUTRAL_RISK_PROMPT,
    CHIEF_RISK_OFFICER_PROMPT
)
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

logger = logging.getLogger(__name__)

class DiscussionService:
    """
    Discussion Service coordinates multi-stage debates (Investment Debate, Risk Debate).
    """
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning = reasoning_service
        logger.info("DiscussionService initialized with multi-stage debate roles")

    async def discuss(self, request: DiscussionRequest) -> DiscussionResponse:
        logger.info(f"DiscussionService starting multi-stage debate for task {request.task_id}")
        opinions: List[AgentOpinion] = []
        
        try:
            # Stage 1: Investment Debate (Bull vs Bear)
            investment_opinions = await self._run_parallel_agents(request, {
                "Bull Researcher": BULL_RESEARCHER_PROMPT,
                "Bear Researcher": BEAR_RESEARCHER_PROMPT
            })
            opinions.extend(investment_opinions)
            
            # Stage 2: Research Manager Synthesizes Investment Plan
            investment_context = request.context_data.copy()
            investment_context["debate"] = "\n".join([o.opinion for o in investment_opinions])
            
            research_manager_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=investment_context,
                prompt=RESEARCH_MANAGER_PROMPT,
                llm_config=request.llm_config
            )
            rm_resp = await self.reasoning.analyze_context(research_manager_req)
            investment_plan = rm_resp.raw_response
            
            opinions.append(AgentOpinion(name="Research Manager", role="research_manager", opinion=investment_plan, confidence=rm_resp.confidence))
            
            # Stage 3: Risk Debate (Aggressive, Conservative, Neutral)
            risk_context = request.context_data.copy()
            risk_context["investment_plan"] = investment_plan
            
            risk_opinions = await self._run_parallel_agents(request, {
                "Aggressive Risk Debator": AGGRESSIVE_RISK_PROMPT,
                "Conservative Risk Debator": CONSERVATIVE_RISK_PROMPT,
                "Neutral Risk Debator": NEUTRAL_RISK_PROMPT
            }, base_context=risk_context)
            opinions.extend(risk_opinions)
            
            # Stage 4: Chief Risk Officer Synthesizes Risk Plan
            risk_debate_context = risk_context.copy()
            risk_debate_context["risk_debate"] = "\n".join([o.opinion for o in risk_opinions])
            
            cro_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=risk_debate_context,
                prompt=CHIEF_RISK_OFFICER_PROMPT,
                llm_config=request.llm_config
            )
            cro_resp = await self.reasoning.analyze_context(cro_req)
            risk_plan = cro_resp.raw_response
            
            opinions.append(AgentOpinion(name="Chief Risk Officer", role="chief_risk_officer", opinion=risk_plan, confidence=cro_resp.confidence))
            
            # The consensus text combines the investment plan and the risk plan
            consensus = f"--- Investment Plan ---\n{investment_plan}\n\n--- Risk Plan ---\n{risk_plan}"
            
            return DiscussionResponse(
                status="success",
                consensus=consensus,
                opinions=opinions
            )
            
        except Exception as e:
            logger.error(f"Discussion failed: {e}")
            return DiscussionResponse(status="failed", error=str(e))
            
    async def _run_parallel_agents(self, request: DiscussionRequest, agent_prompts: dict, base_context: dict = None) -> List[AgentOpinion]:
        context = base_context if base_context is not None else request.context_data
        tasks = []
        keys = []
        for name, prompt in agent_prompts.items():
            req = ReasoningRequest(
                task_id=request.task_id,
                context_data=context,
                prompt=prompt,
                llm_config=request.llm_config
            )
            tasks.append(self.reasoning.analyze_context(req))
            keys.append(name)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        opinions = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Agent {keys[i]} failed: {res}")
                continue
            opinions.append(AgentOpinion(
                name=keys[i],
                role="debator",
                opinion=res.raw_response,
                confidence=res.confidence
            ))
        return opinions
