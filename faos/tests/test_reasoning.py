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


def test_extract_retry_delay():
    service = ReasoningService()
    
    err1 = "[LLM Error] 429 RESOURCE_EXHAUSTED. {'retryDelay': '29s'}"
    delay1 = service._extract_retry_delay(err1, attempt=0)
    assert delay1 == 30.0  # 29 + 1.0 buffer

    err2 = "Quota exceeded... Please retry in 15.5s."
    delay2 = service._extract_retry_delay(err2, attempt=0)
    assert delay2 == 16.5  # 15.5 + 1.0 buffer

    err3 = "429 Too Many Requests"
    delay3 = service._extract_retry_delay(err3, attempt=1, base_delay=3.0)
    assert delay3 == 6.0  # 3.0 * (2 ** 1)


@pytest.mark.asyncio
async def test_gemini_retry_on_rate_limit(monkeypatch):
    service = ReasoningService()
    service.provider = "gemini"
    
    class FakeResponse:
        text = "Retried successfully"
        usage_metadata = None
    call_count = 0

    class FakeClient:
        class aio:
            class models:
                async def generate_content_stream(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1:
                        raise Exception("429 RESOURCE_EXHAUSTED. 'retryDelay': '0.1s'")
                    class FakeChunk:
                        text = "Retried "
                    class FakeChunk2:
                        text = "successfully"
                    yield FakeChunk()
                    yield FakeChunk2()
    
    service._client = FakeClient()
    
    request = ReasoningRequest(
        task_id="retry-test-1",
        context_data={}
    )
    
    # Sleep should be fast because retryDelay is 0.1s + 1s buffer = 1.1s
    response = await service.analyze_context(request)
    assert call_count == 2
    assert response.raw_response == "Retried successfully"

from pydantic import BaseModel, Field

class DummyStructured(BaseModel):
    name: str
    score: float

@pytest.mark.asyncio
async def test_analyze_structured_retry_on_bad_json(monkeypatch):
    service = ReasoningService()
    service.provider = "gemini"
    
    call_count = 0
    
    class FakeBadResponse:
        raw_response = "I am a bad LLM, here is some text instead of JSON!"
        
    class FakeGoodResponse:
        raw_response = '{"name": "test", "score": 9.5}'
        
    async def mock_analyze_context(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return FakeBadResponse()
        return FakeGoodResponse()
        
    # Monkeypatch the internal analyze_context
    monkeypatch.setattr(service, "analyze_context", mock_analyze_context)
    
    req = ReasoningRequest(task_id="retry-json", context_data={})
    parsed, raw = await service.analyze_structured(req, DummyStructured)
    
    assert call_count == 2
    assert parsed is not None
    assert parsed.name == "test"
    assert parsed.score == 9.5
