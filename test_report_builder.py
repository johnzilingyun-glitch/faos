import asyncio
from faos.services.report.service import ReportService
from faos.services.report.models import ReportRequest

async def test_report():
    service = ReportService()
    
    context_data = {
        "analysis": {
            "symbol": "AAPL",
            "price": 150.0,
            "target_price": 165.0,
            "sentiment": 0.8
        },
        "decision": {
            "action": "BUY",
            "confidence": 0.85,
            "strategy": "Buy at current market price",
            "risk": 30,
            "reason": "Strong fundamentals and positive news sentiment",
            "evidence": ["Revenue grew by 20%", "New product launch successful"]
        }
    }
    
    req_md = ReportRequest(task_id="test-123", context_data=context_data, format="markdown")
    res_md = await service.generate(req_md)
    
    print("--- Markdown Output ---")
    print(res_md.content)
    print("\n")
    
    req_json = ReportRequest(task_id="test-123", context_data=context_data, format="json")
    res_json = await service.generate(req_json)
    
    print("--- JSON Output ---")
    print(res_json.content)
    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_report())
