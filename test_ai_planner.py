import asyncio
import os
import json
from faos.core.runtime import TaskRuntime

async def main():
    # Force Mock provider for deterministic behavior
    os.environ["FAOS_LLM_PROVIDER"] = "mock"
    
    runtime = TaskRuntime()
    runtime.start()
    
    # Let's monkeypatch the mock reasoning service to simulate LLM planning
    original_analyze = runtime.reasoning.analyze_context
    
    async def mock_planner_analyze(request):
        if "available_workflows" in request.context_data:
            intent = request.context_data["intent"]
            print(f"\n[Mock LLM] Parsing intent: {intent}")
            
            if "news" in intent.lower():
                response_json = {
                    "workflow_id": "NewsSummaryWorkflow",
                    "parameters": {"symbol": "TSLA"},
                    "reasoning": "User asked for news specifically, choosing NewsSummaryWorkflow."
                }
            else:
                response_json = {
                    "workflow_id": "AnalyzeStockWorkflow",
                    "parameters": {"symbol": "AAPL"},
                    "reasoning": "General stock analysis intent, choosing AnalyzeStockWorkflow."
                }
                
            from faos.services.reasoning.models import ReasoningResponse
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.9,
                raw_response=json.dumps(response_json),
                usage={}
            )
        return await original_analyze(request)
        
    runtime.reasoning.analyze_context = mock_planner_analyze

    print("\n--- Test 1: General Analysis Intent ---")
    task1 = await runtime.submit_task("I want to know about AAPL", {})
    await asyncio.sleep(0.5)  # Wait for planner to run
    
    print("\n--- Test 2: News Specific Intent ---")
    task2 = await runtime.submit_task("Summarize the latest news for TSLA", {})
    await asyncio.sleep(0.5)

    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
