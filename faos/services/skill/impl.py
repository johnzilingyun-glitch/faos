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
            capability="FetchData",
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
            name="Mock News Skill",
            capability="FetchNews",
            description="Mock implementation of fetching news data"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        symbol = request.parameters.get("symbol", "AAPL")
        
        provider_req = ProviderRequest(entity=symbol)
        provider_resp = await self.data_route.fetch_data("news", provider_req)
        
        if provider_resp.status == "failed":
            return SkillResponse(status="failed", error=provider_resp.error)
            
        request.context.add_provider_output("news", provider_resp.data)
        return SkillResponse(status="success", output={"data_type": "news"})


class AnalyzeSkill(BaseSkill):
    def __init__(self, analyze_service):
        self.analyze_service = analyze_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.analyze.reasoning",
            name="Reasoning Analyze Skill",
            capability="Analyze",
            description="Uses AnalyzeService to analyze stock from 4 different perspectives"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.analyze.models import AnalyzeRequest
        analyze_req = AnalyzeRequest(
            task_id=request.task_id,
            context_data=request.context.provider_outputs,
            llm_config=request.context.get_variable("llm_config", {})
        )
        response = await self.analyze_service.analyze(analyze_req)
        
        request.context.add_result("analysis_reports", response.analyst_reports)
        return SkillResponse(status="success", output=response.analyst_reports)


class DecisionSkill(BaseSkill):
    def __init__(self, decision_service: DecisionService):
        self.decision_service = decision_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.decision.policy",
            name="Policy Decision Skill",
            capability="Decision",
            description="Uses DecisionService to make investment decisions"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        decision_req = DecisionRequest(
            task_id=request.task_id,
            reasoning_results=request.context.results,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        result = await self.decision_service.evaluate(decision_req)
        
        decision_data = {
            "action": result.action,
            "confidence": result.confidence,
            "reason": result.reason,
            "risk": result.risk,
            "strategy": result.strategy
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
            capability="GenerateReport",
            description="Generates markdown report using ReportService"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.report.models import ReportRequest
        
        # Get requested format from parameters or default to markdown
        format_type = request.parameters.get("format", "markdown")
        
        report_req = ReportRequest(
            task_id=request.task_id,
            context_data=request.context.results,
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
            capability="Discussion",
            description="Orchestrates expert agents to form consensus"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        from faos.services.discussion.models import DiscussionRequest
        
        # Pull data from context to discuss
        context_data = request.context.provider_outputs.copy()
        context_data["analysis_reports"] = request.context.results.get("analysis_reports", {})
        
        disc_req = DiscussionRequest(
            task_id=request.task_id,
            context_data=context_data,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        response = await self.discussion.discuss(disc_req)
        
        if response.status == "failed":
            return SkillResponse(status="failed", error=response.error)
            
        request.context.add_result("discussion", response.model_dump())
        
        return SkillResponse(status="success", output={"consensus": response.consensus})


class ReflectionSkill(BaseSkill):
    def __init__(self, reflection_service):
        self.reflection_service = reflection_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.reflection.risk",
            name="Reflection Risk Skill",
            capability="Reflection",
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
