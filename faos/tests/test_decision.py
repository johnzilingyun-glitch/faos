import pytest
from unittest.mock import AsyncMock
from faos.services.decision.models import DecisionRequest, DecisionResult
from faos.services.decision.service import DecisionService
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningResponse

@pytest.fixture
def mock_reasoning():
    reasoning = ReasoningService()
    
    async def mock_analyze(req):
        # We simulate the portfolio manager responding with BUY
        if "Portfolio Manager" in req.prompt:
            return ReasoningResponse(
                task_id=req.task_id,
                insights={"symbol": "AAPL"},
                confidence=0.85,
                raw_response="I have reviewed the inputs and decided to BUY the asset.",
                usage={"total_tokens": 100}
            )
        # Simulate Trader
        return ReasoningResponse(
            task_id=req.task_id,
            insights={"symbol": "AAPL"},
            confidence=0.9,
            raw_response="Trader proposal: Entry at $150, Stop Loss at $140.",
            usage={"total_tokens": 100}
        )
        
    reasoning.analyze_context = AsyncMock(side_effect=mock_analyze)
    return reasoning

@pytest.mark.asyncio
async def test_decision_service_trader_and_pm(mock_reasoning):
    service = DecisionService(mock_reasoning)
    
    request = DecisionRequest(
        task_id="test-task-1",
        reasoning_results={"discussion": {"consensus": "Bullish investment plan and conservative risk plan."}}
    )
    
    result = await service.evaluate(request)
    
    assert isinstance(result, DecisionResult)
    # The portfolio manager mock returned "BUY"
    assert result.action == "BUY"
    assert result.confidence == 0.85
    assert "Trader proposal" in result.strategy
    
    # 2 calls: 1 for Trader, 1 for Portfolio Manager
    assert mock_reasoning.analyze_context.call_count == 2
