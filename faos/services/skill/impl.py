import asyncio
from faos.services.skill.base import BaseSkill
from faos.services.skill.models import SkillRequest, SkillResponse, SkillManifest
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.services.provider.service import ProviderService
from faos.services.provider.models import ProviderRequest
from faos.services.decision.service import DecisionService
from faos.services.decision.models import DecisionRequest

class FetchDataSkill(BaseSkill):
    def __init__(self, data_route):
        self.data_route = data_route
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.quote.mock",
            name="Mock Quote Skill",
            capability="cap.fetch_data",
            description="Mock implementation of fetching quote data"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        symbol = request.parameters.get("symbol", "AAPL")
        
        provider_req = ProviderRequest(entity=symbol)
        provider_resp = await self.data_route.fetch_data("market", provider_req)
        
        if provider_resp.status == "failed":
            return SkillResponse(status="failed", error=provider_resp.error)
        
        # Skill writes to ExecutionContext as per architecture
        request.context.add_provider_output("quote", provider_resp.data)
        return SkillResponse(status="success", output={"data_type": "quote"})


class FetchNewsSkill(BaseSkill):
    def __init__(self, data_route):
        self.data_route = data_route
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.news.mock",
            name="News Fetching Skill",
            capability="cap.fetch_news",
            description="Fetches real-time financial, macroeconomic, geopolitical, and morning digest news from major media sources."
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        params = request.parameters or {}
        symbol = params.get("symbol", "AAPL")
        search_query = params.get("search_query")
        news_sources = params.get("news_sources", [])
        news_type = params.get("news_type", "general")
        
        provider_req = ProviderRequest(
            entity=symbol,
            parameters={
                "search_query": search_query,
                "news_sources": news_sources,
                "news_type": news_type,
            }
        )
        
        # 1. Fetch web news (Tavily / Serper News / Jina with targeted sources)
        web_resp = await self.data_route.fetch_data("news", provider_req)
        
        results = []
        if web_resp.status == "success" and isinstance(web_resp.data, list):
            results.extend(web_resp.data)
            
        # 2. Also fetch yfinance news if symbol is a valid stock ticker and query is not custom
        if symbol and not search_query:
            try:
                yf_req = ProviderRequest(entity=symbol)
                yf_resp = await self.data_route.provider_service.fetch_data("yfinance_news", yf_req)
                if yf_resp.status == "success" and isinstance(yf_resp.data, list):
                    existing_titles = {item.get("title", "").lower() for item in results if isinstance(item, dict)}
                    for item in yf_resp.data:
                        if isinstance(item, dict) and item.get("title", "").lower() not in existing_titles:
                            results.append(item)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Secondary yfinance news fetch skipped: {e}")
                
        request.context.add_provider_output("news", results)
        return SkillResponse(status="success", output={"data_type": "news", "count": len(results)})


class AnalyzeSkill(BaseSkill):
    def __init__(self, analyze_service):
        self.analyze_service = analyze_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.analyze.reasoning",
            name="Reasoning Analyze Skill",
            capability="cap.analyze",
            description="Uses AnalyzeService to analyze stock from 4 different perspectives"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.analyze.models import AnalyzeRequest
        from faos.services.reasoning.schemas import build_fact_sheet

        context_data = request.context.provider_outputs.copy()
        context_data["user_parameters"] = request.parameters

        # Build the canonical FactSheet ONCE and inject it so downstream agents
        # reference established facts instead of re-introducing the company.
        fact_sheet = build_fact_sheet(request.context.provider_outputs, request.parameters)
        context_data["fact_sheet"] = fact_sheet
        request.context.set_fact_sheet(fact_sheet)

        analyze_req = AnalyzeRequest(
            task_id=request.task_id,
            context_data=context_data,
            llm_config=request.context.get_variable("llm_config", {})
        )
        response = await self.analyze_service.analyze(analyze_req)

        # Rendered markdown (back-compat for report builder + frontend)
        request.context.add_result("analysis_reports", response.analyst_reports)
        # Structured reports (new, for evidence fusion / downstream agents)
        request.context.add_result(
            "analysis_reports_structured",
            {role: rep.model_dump() for role, rep in response.structured_reports.items()}
        )

        # Populate the shared evidence graph (Fact -> Inference chain).
        for role, rep in response.structured_reports.items():
            for f in rep.facts:
                request.context.add_evidence_node("facts", {**f.model_dump(), "by": role})
            for e in rep.evidence:
                request.context.add_evidence_node("evidence", {**e.model_dump(), "by": role})
            for s in rep.signals:
                request.context.add_evidence_node("signals", {**s.model_dump(), "by": role})
            for i in rep.inferences:
                request.context.add_evidence_node("inferences", {**i.model_dump(), "by": role})

        return SkillResponse(status="success", output=response.analyst_reports)


class DecisionSkill(BaseSkill):
    def __init__(self, decision_service: DecisionService):
        self.decision_service = decision_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.decision.policy",
            name="Policy Decision Skill",
            capability="cap.decision",
            description="Uses DecisionService to make investment decisions"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        reasoning_results = request.context.results.copy()
        reasoning_results["user_parameters"] = request.parameters
        
        context_data = request.context.provider_outputs.copy()
        context_data["provider_outputs"] = request.context.provider_outputs.copy()
        
        decision_req = DecisionRequest(
            task_id=request.task_id,
            reasoning_results=reasoning_results,
            context_data=context_data,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        result = await self.decision_service.evaluate(decision_req)
        
        decision_data = {
            "action": result.action,
            "confidence": result.confidence,
            "reason": result.reason,
            "risk": result.risk,
            "strategy": result.strategy,
            "scorecard": result.scorecard
        }
        
        request.context.add_result("decision", decision_data)
        return SkillResponse(status="success", output=decision_data)


class GenerateReportSkill(BaseSkill):
    def __init__(self, report_service):
        self.report_service = report_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.report.markdown",
            name="Markdown Report Skill",
            capability="cap.report",
            description="Generates markdown report using ReportService"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.report.models import ReportRequest
        
        # Get requested format from parameters or default to markdown
        format_type = request.parameters.get("format", "markdown")
        
        context_data = request.context.results.copy()
        context_data["provider_outputs"] = request.context.provider_outputs.copy()
        context_data["user_parameters"] = request.parameters
        # Canonical FactSheet + shared evidence graph for de-duplicated rendering.
        context_data["fact_sheet"] = request.context.fact_sheet
        context_data["evidence_graph"] = request.context.evidence_graph
        
        report_req = ReportRequest(
            task_id=request.task_id,
            context_data=context_data,
            format=format_type
        )
        
        response = await self.report_service.generate(report_req)
        
        if response.status == "failed":
            return SkillResponse(status="failed", error=response.error)
            
        request.context.add_result("report", response.content)
        
        preview = str(response.content)[:100] + "..." if isinstance(response.content, str) else "JSON output"
        return SkillResponse(status="success", output={"report_preview": preview})

class DiscussSkill(BaseSkill):
    def __init__(self, discussion_service):
        self.discussion = discussion_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.discuss",
            name="Multi-Agent Discussion Skill",
            capability="cap.discuss",
            description="Orchestrates expert agents to form consensus"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.discussion.models import DiscussionRequest
        
        # Pull data from context to discuss
        context_data = request.context.provider_outputs.copy()
        context_data["analysis_reports"] = request.context.results.get("analysis_reports", {})
        context_data["user_parameters"] = request.parameters
        # Reuse the canonical FactSheet so debaters don't re-introduce the company.
        if request.context.fact_sheet:
            context_data["fact_sheet"] = request.context.fact_sheet
        
        disc_req = DiscussionRequest(
            task_id=request.task_id,
            context_data=context_data,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        response = await self.discussion.discuss(disc_req)
        
        if response.status == "failed":
            return SkillResponse(status="failed", error=response.error)
            
        # Map opinions to frontend expected structure
        frontend_discussion = {
            "Investment Debate": {},
            "Investment Plan": "",
            "Risk Debate": {},
            "Risk Plan": ""
        }
        
        for op in response.opinions:
            if op.name == "Bull Researcher":
                frontend_discussion["Investment Debate"]["Bull"] = op.opinion
            elif op.name == "Bear Researcher":
                frontend_discussion["Investment Debate"]["Bear"] = op.opinion
            elif op.name == "Research Manager":
                frontend_discussion["Investment Plan"] = op.opinion
            elif op.name == "Chief Risk Officer":
                frontend_discussion["Risk Plan"] = op.opinion
            elif "Risk Debator" in op.name:
                frontend_discussion["Risk Debate"][op.name] = op.opinion

        # Persist the structured debate into the shared evidence graph (claims / rebuttals).
        for op in response.opinions:
            if not op.structured:
                continue
            if op.name == "Bull Researcher":
                for c in op.structured.get("claims", []):
                    request.context.add_evidence_node("claims", {**c, "by": "bull"})
            elif op.name == "Bear Researcher":
                for r in op.structured.get("rebuttals", []):
                    request.context.add_evidence_node("claims", {**r, "by": "bear", "kind": "rebuttal"})

        request.context.add_result("discussion", frontend_discussion)
        request.context.add_result(
            "debate_structured",
            {op.name: op.structured for op in response.opinions if op.structured}
        )
        
        return SkillResponse(status="success", output={"consensus": response.consensus})


class ReflectionSkill(BaseSkill):
    def __init__(self, reflection_service):
        self.reflection_service = reflection_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.reflection.risk",
            name="Reflection Risk Skill",
            capability="cap.reflection",
            description="Uses ReflectionService to perform hallucination and logic checks"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.reflection.models import ReflectionRequest
        
        target_data = request.context.results.copy()
        
        reflection_req = ReflectionRequest(
            task_id=request.task_id,
            target_data=target_data,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        result = await self.reflection_service.evaluate(reflection_req)
        
        reflection_data = {
            "is_passed": result.is_passed,
            "confidence": result.confidence,
            "feedback": result.feedback
        }
        if result.revised_data:
            reflection_data["revised_data"] = result.revised_data
            
        request.context.add_result("reflection", reflection_data)
            
        return SkillResponse(status="success", output={"feedback": result.feedback, "is_passed": result.is_passed})
