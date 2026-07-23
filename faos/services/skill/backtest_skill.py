import logging
from faos.services.skill.base import BaseSkill
from faos.services.skill.models import SkillRequest, SkillResponse
from faos.core.models import Event
from faos.services.decision.portfolio import PortfolioTracker
import asyncio
from faos.services.decision.portfolio import PortfolioTracker
import asyncio

logger = logging.getLogger(__name__)

class BacktestInitSkill(BaseSkill):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        
    @property
    def manifest(self):
        from faos.services.skill.models import SkillManifest
        return SkillManifest(
            id="skill.backtest.init",
            name="Backtest Init Skill",
            capability="cap.init_backtest"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        logger.info("Initializing Backtest Environment")
        # Use request parameters instead of payload
        context = request.context
        task_id = request.task_id
        
        # Initialize Portfolio Tracker in context
        portfolio = PortfolioTracker(initial_cash=100000.0)
        context.variables["portfolio"] = portfolio
        context.variables["backtest_dates"] = ["2026-06-05", "2026-06-12", "2026-06-19", "2026-06-26"] # Mock dates for MVP
        
        return SkillResponse(status="success", output={"status": "initialized"})

class BacktestLoopSkill(BaseSkill):
    def __init__(self, event_bus):
        super().__init__()
        self.event_bus = event_bus
        
    @property
    def manifest(self):
        from faos.services.skill.models import SkillManifest
        return SkillManifest(
            id="skill.backtest.loop",
            name="Backtest Loop Skill",
            capability="cap.run_backtest_loop"
        )
        
    async def execute(self, request: SkillRequest) -> SkillResponse:
        logger.info("Running Backtest Time Loop")
        context = request.context
        task_id = request.task_id
        
        portfolio: PortfolioTracker = context.variables.get("portfolio")
        dates = context.variables.get("backtest_dates", [])
        symbol = request.parameters.get("symbol", "Unknown")
        
        # Simulate time loop (MVP: Mocking the LLM decision to avoid excessive API calls)
        for date in dates:
            logger.info(f"--- Backtest Date: {date} ---")
            
            # 1. Fetch data for this date slice (mocked)
            price = 150.0  # mock price
            
            # 2. Simulate a decision logic (in reality, calls ReasoningService)
            # For MVP, we will just simulate a basic moving average crossover or random decision
            action = "BUY" if len(portfolio.holdings) == 0 else "HOLD"
            confidence = 0.8
            
            # 3. Execute Trade
            portfolio.execute_trade(date, symbol, action, price, confidence)
            
            # 4. Snapshot
            portfolio.snapshot(date, {symbol: price})
            
            # Sleep slightly to simulate processing
            await asyncio.sleep(0.1)
            
        metrics = portfolio.get_metrics()
        context.add_result("backtest_metrics", metrics)
        
        return SkillResponse(status="success", output={"metrics": metrics})
