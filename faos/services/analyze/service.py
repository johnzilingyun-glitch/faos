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
from faos.services.reasoning.schemas import AnalystReport, ANALYST_REPORT_JSON_HINT
from faos.services.security.grounding import verify_and_annotate
from faos.services.security.guardrail import check_guardrails

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
            # Each analyst gets its own shallow copy so PromptBuilder can safely
            # pop fact_sheet/user_parameters without affecting the others.
            req = ReasoningRequest(
                task_id=request.task_id,
                context_data=dict(request.context_data),
                prompt=prompt,
                llm_config=request.llm_config
            )
            tasks.append(self._run_analyst(name, req))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        rendered = {}
        structured = {}
        for res in results:
            if isinstance(res, Exception):
                # In real scenario, log error
                continue
            rendered[res["name"]] = res["rendered"]
            structured[res["name"]] = res["structured"]
            
        return AnalyzeResponse(
            task_id=request.task_id,
            status="success",
            analyst_reports=rendered,
            structured_reports=structured
        )
        
    async def _run_analyst(self, name: str, req: ReasoningRequest):
        lang = (req.context_data.get("user_parameters", {}) or {}).get("language", "zh")
        report, raw = await self.reasoning_service.analyze_structured(
            req, AnalystReport, ANALYST_REPORT_JSON_HINT
        )
        if report is None:
            # Structured parse failed: degrade gracefully, keep the raw text.
            report = AnalystReport(summary=raw)
            
        report.role = name
        
        # 1. Output Guardrail (Logic interception)
        guard_res = check_guardrails(report)
        if guard_res.action == "block":
            import logging
            logging.getLogger(__name__).warning(f"Guardrail blocked output from {name}: {guard_res.reason}")
            # Rewrite the summary with the block message
            report.summary = (
                f"> [!CAUTION]\n> **[FAOS Guardrail Blocked]** 该分析结论未通过安全校验，已被强行拦截。\n"
                f"> **拦截原因**: {guard_res.reason}\n\n"
                f"~~{report.summary}~~"
            )
            report.action = "watch" # Downgrade action
            
        # 2. Grounding Verifier (Anti-hallucination)
        fact_sheet = req.context_data.get("fact_sheet", {})
        report.summary = verify_and_annotate(report.summary, fact_sheet)

        return {
            "name": name,
            "structured": report,
            "rendered": report.render(lang)
        }
