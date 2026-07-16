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
    def __init__(self, provider_service: ProviderService):
        self.provider_service = provider_service
        
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
        provider_resp = await self.provider_service.fetch_by_category("market", provider_req)
        
        if provider_resp.status == "failed":
            return SkillResponse(status="failed", error=provider_resp.error)
        
        # Skill writes to ExecutionContext as per architecture
        request.context.add_provider_output("quote", provider_resp.data)
        return SkillResponse(status="success", output={"data_type": "quote"})


class FetchNewsSkill(BaseSkill):
    def __init__(self, provider_service: ProviderService):
        self.provider_service = provider_service
        
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
        provider_resp = await self.provider_service.fetch_by_category("news", provider_req)
        
        if provider_resp.status == "failed":
            return SkillResponse(status="failed", error=provider_resp.error)
            
        request.context.add_provider_output("news", provider_resp.data)
        return SkillResponse(status="success", output={"data_type": "news"})


class AnalyzeSkill(BaseSkill):
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning_service = reasoning_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="stock.analyze.reasoning",
            name="Reasoning Analyze Skill",
            capability="Analyze",
            description="Uses ReasoningService to analyze stock"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        reasoning_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=request.context.provider_outputs
        )
        response = await self.reasoning_service.analyze_context(reasoning_req)
        
        request.context.add_result("analysis", response.insights)
        return SkillResponse(status="success", output=response.insights)


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
        analysis = request.context.results.get("analysis", {})
        
        decision_req = DecisionRequest(
            task_id=request.task_id,
            reasoning_results=analysis
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
