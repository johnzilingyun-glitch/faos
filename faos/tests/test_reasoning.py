import pytest
import asyncio
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

@pytest.mark.asyncio
async def test_reasoning_service_analyze_context_with_news():
    service = ReasoningService()
    
    request = ReasoningRequest(
        task_id="test-task-1",
        context_data={
            "quote": {"symbol": "AAPL", "price": 150.0},
            "news": [
                {"title": "Good news", "sentiment": 0.8},
                {"title": "More good news", "sentiment": 0.6}
            ]
        }
    )
    
    response = await service.analyze_context(request)
    
    assert response.task_id == "test-task-1"
    assert response.insights["symbol"] == "AAPL"
    assert response.insights["sentiment"] == 0.7  # (0.8 + 0.6) / 2
    assert "recommendation" not in response.insights
    assert response.confidence == 0.85
    assert "estimated" in response.raw_response

@pytest.mark.asyncio
async def test_reasoning_service_analyze_context_without_news():
    service = ReasoningService()
    
    request = ReasoningRequest(
        task_id="test-task-2",
        context_data={
            "quote": {"symbol": "TSLA", "price": 200.0}
        }
    )
    
    response = await service.analyze_context(request)
    
    assert response.task_id == "test-task-2"
    assert response.insights["symbol"] == "TSLA"
    assert response.insights["sentiment"] == 0.0
    assert "recommendation" not in response.insights
    assert response.confidence == 0.50
    assert "estimated" in response.raw_response
