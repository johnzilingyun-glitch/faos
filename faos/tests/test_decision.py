import pytest
from faos.services.decision.models import DecisionRequest, DecisionResult
from faos.services.decision.service import DecisionService

@pytest.mark.asyncio
async def test_decision_service_evaluate_buy():
    service = DecisionService()
    
    request = DecisionRequest(
        task_id="test-task-1",
        reasoning_results={"sentiment": 0.8}
    )
    
    result = await service.evaluate(request)
    
    assert isinstance(result, DecisionResult)
    assert result.action == "BUY"
    assert result.confidence == 0.8
    assert "Positive sentiment" in result.reason

@pytest.mark.asyncio
async def test_decision_service_evaluate_sell():
    service = DecisionService()
    
    request = DecisionRequest(
        task_id="test-task-2",
        reasoning_results={"sentiment": 0.2}
    )
    
    result = await service.evaluate(request)
    
    assert result.action == "SELL"
    assert result.confidence == 0.8
    assert "Negative sentiment" in result.reason

@pytest.mark.asyncio
async def test_decision_service_evaluate_hold():
    service = DecisionService()
    
    request = DecisionRequest(
        task_id="test-task-3",
        reasoning_results={"sentiment": 0.5}
    )
    
    result = await service.evaluate(request)
    
    assert result.action == "HOLD"
    assert result.confidence == 0.5
    assert "Neutral" in result.reason
