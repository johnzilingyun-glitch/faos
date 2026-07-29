import pytest
import asyncio
from faos.services.reasoning.token_guard import token_guard, compact_json
from faos.services.reasoning.context_builder import ContextBuilder
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

def test_token_guard_truncation():
    """Test that TokenGuard properly truncates long inputs."""
    token_guard.set_level("high")  # Should cap tools to 4000
    
    long_news = "A" * 10000
    safe_news = token_guard.enforce("get_news", long_news)
    
    # "get_news" has max_chars=5000 in "high" level (1.0 multiplier)
    assert len(safe_news) < 6000
    assert "truncated" in safe_news
    assert safe_news.startswith("A" * 1000)
    
def test_context_builder():
    """Test that ContextBuilder correctly limits and formats contexts."""
    quote = {"symbol": "AAPL", "price": 150.0, "volume": 1000000}
    news = [{"headline": "Apple is doing well", "body": "B" * 6000}]
    
    token_guard.set_level("high")
    ctx = ContextBuilder.assemble_context(symbol="AAPL", quote=quote, news=news)
    
    assert ctx["user_parameters"]["symbol"] == "AAPL"
    assert "150.0" in ctx["quote_str"]
    assert len(ctx["news_str"]) < 5500  # Should be truncated

@pytest.mark.asyncio
async def test_reasoning_service_fallback():
    """Test that ReasoningService falls back correctly in mock mode."""
    # We will test that it does not crash when using mock
    service = ReasoningService()
    service.provider = "mock"
    
    request = ReasoningRequest(
        task_id="test_fallback",
        context_data={"symbol": "AAPL"}
    )
    
    # In mock mode it should just return mock response
    resp = await service.analyze_context(request)
    assert resp.confidence >= 0.0
    assert "target price" in resp.raw_response.lower()
