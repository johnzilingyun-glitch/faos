import logging
from typing import List

from faos.services.discussion.models import DiscussionRequest, DiscussionResponse, AgentOpinion
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

logger = logging.getLogger(__name__)

class DiscussionService:
    """
    Discussion Service coordinates multiple virtual agents (Fundamental, Technical, Risk)
    to analyze the data and synthesize a consensus.
    """
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning = reasoning_service
        logger.info("DiscussionService initialized")
        
        self.agents = [
            {
                "name": "Fundamental Analyst",
                "role": "fundamental",
                "prompt": (
                    "You are a Fundamental Analyst researcher tasked with analyzing fundamental information about a company or asset. "
                    "Please write a comprehensive report of the fundamental information such as financial documents, valuation, "
                    "earnings, and macroeconomic factors to inform trading strategies. Make sure to include as much detail as possible. "
                    "Provide specific, actionable insights with supporting evidence. "
                    "Make sure to append a Markdown table at the end of the report to organize key points, making it organized and easy to read. "
                    "Note: Do NOT produce a final investment decision (like BUY/HOLD/SELL); your role is strictly to provide reasoning and analysis."
                )
            },
            {
                "name": "Technical Analyst",
                "role": "technical",
                "prompt": (
                    "You are a Technical Analyst trading assistant tasked with analyzing financial markets and price action. "
                    "Please write a comprehensive report on the current market trends, analyzing key indicators such as moving averages, "
                    "momentum, volume, and volatility. Identify key support and resistance levels. "
                    "Provide specific, actionable insights with supporting evidence to help traders make informed decisions. "
                    "Make sure to append a Markdown table at the end of the report to organize key points, making it organized and easy to read. "
                    "Note: Do NOT produce a final investment decision (like BUY/HOLD/SELL); your role is strictly to provide reasoning and analysis."
                )
            },
            {
                "name": "Risk Manager",
                "role": "risk",
                "prompt": (
                    "You are a Risk Manager tasked with evaluating the downside risks and potential exposure of trading an asset. "
                    "Please write a comprehensive report assessing volatility, historical drawdowns, market sentiment extremes, "
                    "and potential systemic or idiosyncratic risks. "
                    "Provide specific, actionable insights with supporting evidence to ensure safe portfolio management. "
                    "Make sure to append a Markdown table at the end of the report to organize key points, making it organized and easy to read. "
                    "Note: Do NOT produce a final investment decision (like BUY/HOLD/SELL); your role is strictly to provide risk reasoning and analysis."
                )
            }
        ]

    async def discuss(self, request: DiscussionRequest) -> DiscussionResponse:
        logger.info(f"DiscussionService starting multi-agent debate for task {request.task_id}")
        
        opinions: List[AgentOpinion] = []
        
        try:
            # 1. Ask each expert agent for their opinion
            for agent in self.agents:
                logger.info(f"Invoking {agent['name']}...")
                reasoning_req = ReasoningRequest(
                    task_id=request.task_id,
                    context_data=request.context_data,
                    prompt=f"{agent['prompt']}"
                )
                
                # In a real system, these could be executed concurrently with asyncio.gather
                resp = await self.reasoning.analyze_context(reasoning_req)
                
                opinion = AgentOpinion(
                    name=agent["name"],
                    role=agent["role"],
                    opinion=resp.raw_response,
                    confidence=resp.confidence
                )
                opinions.append(opinion)
                
            # 2. Synthesize a consensus
            logger.info("Synthesizing final consensus via ReasoningService...")
            
            consensus_prompt = (
                "You are a Head of Trading Committee. Review the following expert opinions from your team "
                "(Fundamental Analyst, Technical Analyst, Risk Manager). "
                "Synthesize their views into a unified consensus report. "
                "Highlight areas of agreement and note any conflicting viewpoints. "
                "Make sure to append a Markdown table summarizing the combined insights. "
                "Do NOT produce a final investment decision (like BUY/HOLD/SELL), just the synthesized reasoning."
            )
            
            opinions_text = "\n\n".join([f"--- {o.name} ---\n{o.opinion}" for o in opinions])
            
            consensus_req = ReasoningRequest(
                task_id=request.task_id,
                context_data={"expert_opinions": opinions_text},
                prompt=consensus_prompt
            )
            
            consensus_resp = await self.reasoning.analyze_context(consensus_req)
            consensus_text = consensus_resp.raw_response
                
            return DiscussionResponse(
                status="success",
                consensus=consensus_text,
                opinions=opinions
            )
            
        except Exception as e:
            logger.error(f"Discussion failed: {e}")
            return DiscussionResponse(status="failed", error=str(e))
