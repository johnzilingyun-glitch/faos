import pytest
import json

from faos.services.report.models import ReportRequest
from faos.services.report.service import ReportService

@pytest.fixture
def sample_context_data():
    return {
        "analysis": {
            "symbol": "AAPL",
            "price": 150.0,
            "target_price": 160.0,
            "sentiment": 0.75
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
    assert "FAOS Analysis Report for AAPL" in content
    assert "Current Price**: $150.00" in content
    assert "Action**: **BUY**" in content
    assert "Confidence**: 80.0%" in content

@pytest.mark.asyncio
async def test_report_service_json(sample_context_data):
    service = ReportService()
    request = ReportRequest(task_id="test-2", context_data=sample_context_data, format="json")
    
    response = await service.generate(request)
    
    assert response.status == "success"
    assert response.format == "json"
    
    content = response.content
    assert isinstance(content, dict)
    assert content["metadata"]["generator"] == "FAOS Report Service"
    assert content["data"]["analysis"]["symbol"] == "AAPL"
    assert content["data"]["decision"]["action"] == "BUY"

@pytest.mark.asyncio
async def test_report_service_unsupported_format(sample_context_data):
    service = ReportService()
    request = ReportRequest(task_id="test-3", context_data=sample_context_data, format="pdf")
    
    response = await service.generate(request)
    
    assert response.status == "failed"
    assert "Unsupported report format: pdf" in response.error
