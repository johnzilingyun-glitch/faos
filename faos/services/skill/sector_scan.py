import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from faos.services.skill.base import BaseSkill
from faos.services.skill.models import SkillRequest, SkillResponse, SkillManifest
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.services.provider.service import ProviderService
from faos.services.provider.models import ProviderRequest

class SectorScanResult(BaseModel):
    sector_name: str
    candidates: List[str] = Field(description="List of stock tickers (e.g. NVDA, TSLA, 600519.SS, 0700.HK)")
    rationale: str = Field(description="Why these stocks were chosen")

class SectorScanSkill(BaseSkill):
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning_service = reasoning_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="sector.scan",
            name="Sector Scanner",
            capability="cap.sector_scan",
            description="Scans the sector to find top stock candidates based on criteria."
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        sector = request.parameters.get("sector", "Technology")
        criteria = request.parameters.get("criteria", "undervalued")
        
        prompt = (
            f"You are an expert sector analyst. The user is looking for stocks in the '{sector}' sector "
            f"that match the following criteria: '{criteria}'.\n"
            "Please provide 3-5 top stock ticker candidates that best match this description.\n"
            "Include their ticker symbols (e.g., AAPL for US, 0700.HK for HK, 600519.SS for A-shares).\n"
            "Explain your rationale."
        )
        
        req = ReasoningRequest(
            task_id=request.task_id,
            prompt=prompt,
            context_data={},
            json_mode=True,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        resp = await self.reasoning_service.analyze_structured(req, response_model=SectorScanResult)
        
        request.context.add_result("sector_scan_candidates", resp.candidates)
        request.context.add_result("sector_scan_rationale", resp.rationale)
        return SkillResponse(status="success", output={"candidates": resp.candidates})

class BatchFetchDataSkill(BaseSkill):
    def __init__(self, data_route: ProviderService):
        self.data_route = data_route
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="batch.fetch.data",
            name="Batch Data Fetcher",
            capability="cap.batch_fetch_data",
            description="Fetches data for multiple stocks."
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        candidates = request.context.results.get("sector_scan_candidates", [])
        if not candidates:
            # Fallback
            candidates = ["AAPL", "MSFT"]
            
        all_data = {}
        for symbol in candidates:
            provider_req = ProviderRequest(entity=symbol)
            # Try to fetch market data and news
            market_resp = await self.data_route.fetch_data("market", provider_req)
            news_resp = await self.data_route.fetch_data("news", provider_req)
            
            all_data[symbol] = {
                "market": market_resp.data if market_resp.status == "success" else {},
                "news": news_resp.data if news_resp.status == "success" else []
            }
            
        request.context.add_provider_output("batch_data", all_data)
        return SkillResponse(status="success", output={"symbols_fetched": candidates})

class CompareStocksResult(BaseModel):
    winner: str = Field(description="The ticker symbol of the winning stock")
    runner_up: str = Field(description="The ticker symbol of the runner up stock")
    comparison_analysis: str = Field(description="Detailed comparison between the candidates")
    investment_recommendation: str = Field(description="Final recommendation for the portfolio manager")

class CompareStocksSkill(BaseSkill):
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning_service = reasoning_service
        
    @property
    def manifest(self) -> SkillManifest:
        return SkillManifest(
            id="compare.stocks",
            name="Stock Comparator",
            capability="cap.compare_stocks",
            description="Compares multiple stocks and picks the best one."
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        batch_data = request.context.provider_outputs.get("batch_data", {})
        candidates = request.context.results.get("sector_scan_candidates", [])
        rationale = request.context.results.get("sector_scan_rationale", "")
        sector = request.parameters.get("sector", "Unknown Sector")
        
        prompt = (
            f"You are a Chief Investment Officer. Your sector analyst has provided the following candidates for the '{sector}' sector:\n"
            f"{candidates}\n\n"
            f"Analyst Rationale: {rationale}\n\n"
            f"Here is the market and news data for these candidates:\n"
            f"{json.dumps(batch_data, ensure_ascii=False)}\n\n"
            "Please compare these stocks deeply. Pick a clear winner and a runner up based on fundamentals, momentum, and the original screening criteria.\n"
            "Provide a detailed comparison analysis."
        )
        
        req = ReasoningRequest(
            task_id=request.task_id,
            prompt=prompt,
            context_data={},
            json_mode=True,
            llm_config=request.context.get_variable("llm_config", {})
        )
        
        resp = await self.reasoning_service.analyze_structured(req, response_model=CompareStocksResult)
        
        request.context.add_result("comparison_analysis", resp.comparison_analysis)
        request.context.add_result("winner", resp.winner)
        request.context.add_result("runner_up", resp.runner_up)
        
        # Format a final report
        report = (
            f"# 行业全景扫描报告: {sector}\n\n"
            f"## 候选标的\n"
            f"{', '.join(candidates)}\n\n"
            f"### 筛选逻辑\n"
            f"{rationale}\n\n"
            f"## 深度横向对比\n"
            f"{resp.comparison_analysis}\n\n"
            f"## 最终投资建议\n"
            f"**🏆 优胜者**: {resp.winner}\n\n"
            f"**🥈 备选**: {resp.runner_up}\n\n"
            f"{resp.investment_recommendation}"
        )
        request.context.add_result("report", report)
        
        return SkillResponse(status="success", output={"winner": resp.winner})
