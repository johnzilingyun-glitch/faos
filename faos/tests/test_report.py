import pytest
import json

from faos.services.report.models import ReportRequest
from faos.services.report.service import ReportService

@pytest.fixture
def sample_context_data():
    return {
        "user_parameters": {"symbol": "AAPL", "language": "en"},
        "provider_outputs": {
            "quote": {"symbol": "AAPL", "price": 150.0, "change": 1.25}
        },
        "decision": {
            "action": "BUY",
            "confidence": 0.8,
            "strategy": "Value Investing",
            "risk": "Low",
            "reason": "Strong fundamentals"
        }
    }

@pytest.mark.asyncio
async def test_report_service_markdown(sample_context_data):
    service = ReportService()
    request = ReportRequest(task_id="test-1", context_data=sample_context_data, format="markdown")
    
    response = await service.generate(request)
    
    assert response.status == "success"
    assert response.format == "markdown"
    
    content = response.content
    assert "FAOS Financial Intelligence Report: AAPL" in content
    assert "150.00" in content or "150.0" in content
    assert "BUY" in content
    assert "0.8" in content or "80" in content

@pytest.mark.asyncio
async def test_report_service_json(sample_context_data):
    service = ReportService()
    request = ReportRequest(task_id="test-2", context_data=sample_context_data, format="json")
    
    response = await service.generate(request)
    
    assert response.status == "success"
    assert response.format == "json"
    
    content = json.loads(response.content)
    assert isinstance(content, dict)
    assert content["metadata"]["task_id"] == "test-2"
    assert content["title"] == "FAOS Financial Intelligence Report: AAPL"
    assert any("BUY" in s["content"] for s in content["sections"])

@pytest.mark.asyncio
async def test_report_service_unsupported_format(sample_context_data):
    service = ReportService()
    request = ReportRequest(task_id="test-3", context_data=sample_context_data, format="pdf")
    
    response = await service.generate(request)
    
    assert response.status == "failed"
    assert "Unsupported report format: pdf" in response.error
