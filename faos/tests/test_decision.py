import pytest
from unittest.mock import AsyncMock
from faos.services.decision.models import DecisionRequest, DecisionResult, PMDecision, Scorecard
from faos.services.decision.service import DecisionService
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningResponse

@pytest.fixture
def mock_reasoning():
    reasoning = ReasoningService()
    
    async def mock_analyze(req):
        # Simulate Trader (free-text proposal)
        return ReasoningResponse(
            task_id=req.task_id,
            insights={"symbol": "AAPL"},
            confidence=0.9,
            raw_response="Trader proposal: Entry at $150, Stop Loss at $140.",
            usage={"total_tokens": 100}
        )
        
    reasoning.analyze_context = AsyncMock(side_effect=mock_analyze)

    async def mock_structured(req, response_model, schema_hint=None):
        # Simulate the Portfolio Manager's structured decision
        pm = PMDecision(
            action="BUY", confidence=0.85, risk_score=40,
            rationale="I have reviewed the inputs and decided to BUY the asset.",
            scorecard=Scorecard(investment_score=78, risk_level="medium",
                                catalyst=4, valuation=4, macro=3, recommendation="Buy"),
        )
        return pm, pm.model_dump_json()

    reasoning.analyze_structured = AsyncMock(side_effect=mock_structured)
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
    # The portfolio manager mock returned a structured BUY
    assert result.action == "BUY"
    assert result.confidence == 0.85
    assert result.risk == 40
    assert "Trader proposal" in result.strategy
    # Scorecard flows through to the DecisionResult
    assert result.scorecard["investment_score"] == 78
    assert result.scorecard["recommendation"] == "Buy"
    
    # 1 free-text call (Trader) + 1 structured call (PM)
    assert mock_reasoning.analyze_context.call_count == 1
    assert mock_reasoning.analyze_structured.call_count == 1
