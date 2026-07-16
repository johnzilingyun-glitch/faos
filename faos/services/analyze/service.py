import asyncio
from faos.services.analyze.models import AnalyzeRequest, AnalyzeResponse
from faos.services.analyze.prompts import (
    FUNDAMENTAL_ANALYST_PROMPT,
    MARKET_ANALYST_PROMPT,
    NEWS_ANALYST_PROMPT,
    SENTIMENT_ANALYST_PROMPT
)
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

class AnalyzeService:
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning_service = reasoning_service
        self.analysts = {
            "Fundamental Analyst": FUNDAMENTAL_ANALYST_PROMPT,
            "Technical Analyst": MARKET_ANALYST_PROMPT,
            "News Analyst": NEWS_ANALYST_PROMPT,
            "Sentiment Analyst": SENTIMENT_ANALYST_PROMPT
        }

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        tasks = []
        for name, prompt in self.analysts.items():
            req = ReasoningRequest(
                task_id=request.task_id,
                context_data=request.context_data,
                prompt=prompt
            )
            tasks.append(self._run_analyst(name, req))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        reports = {}
        for res in results:
            if isinstance(res, Exception):
                # In real scenario, log error
                continue
            reports[res["name"]] = res["report"]
            
        return AnalyzeResponse(
            task_id=request.task_id,
            status="success",
            analyst_reports=reports
        )
        
    async def _run_analyst(self, name: str, req: ReasoningRequest):
        resp = await self.reasoning_service.analyze_context(req)
        return {
            "name": name,
            "report": resp.raw_response
        }
