import pytest
import asyncio
from faos.core.event_bus import EventBus
from faos.core.models import Event
from faos.execution.planner import PlannerPipeline

from faos.services.workflow.service import WorkflowService
from faos.services.workflow.standard import get_analyze_stock_workflow
from faos.services.capability.service import CapabilityService
from faos.services.capability.models import CapabilityManifest
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest, ReasoningResponse

@pytest.mark.asyncio
async def test_planner_pipeline_generates_plan():
    event_bus = EventBus()
    event_bus.start()
    
    workflow_service = WorkflowService()
    workflow_service.register_workflow(get_analyze_stock_workflow())
    
    capability_service = CapabilityService()
    capability_service.register_capability(CapabilityManifest(id="cap.fetch_data", name="FetchData", inputs=["symbol"]))
    capability_service.register_capability(CapabilityManifest(id="cap.fetch_news", name="FetchNews", inputs=["symbol"]))
    capability_service.register_capability(CapabilityManifest(id="cap.analyze", name="Analyze", inputs=[]))
    capability_service.register_capability(CapabilityManifest(id="cap.discuss", name="Discussion", inputs=[]))
    capability_service.register_capability(CapabilityManifest(id="cap.decision", name="Decision", inputs=[]))
    capability_service.register_capability(CapabilityManifest(id="cap.report", name="GenerateReport", inputs=[]))

    class MockReasoningService(ReasoningService):
        async def analyze_context(self, request: ReasoningRequest) -> ReasoningResponse:
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=1.0,
                raw_response='{"status": "ready", "message": "ok", "workflow_id": "AnalyzeStockWorkflow", "parameters": {"symbol": "TSLA"}, "reasoning": "Test"}',
                usage={}
            )
            
    planner = PlannerPipeline(
        event_bus, 
        workflow_service=workflow_service,
        capability_service=capability_service,
        reasoning_service=MockReasoningService()
    )
    
    # We need a way to capture events published by the planner
    captured_events = []
    
    async def capture_handler(event: Event):
        captured_events.append(event)
        
    event_bus.subscribe("ExecutionPlanGenerated", capture_handler)
    
    # Simulate a TaskSubmitted event with intent that matches regex
    task_submitted_event = Event(
        type="TaskSubmitted",
        source="Test",
        payload={"task_id": "task-planner-123", "intent": "Analyze TSLA"}
    )
    
    await event_bus.publish(task_submitted_event)
    
    # Allow time for event loop to process
    await asyncio.sleep(0.1)
    
    # Stop the event bus to flush
    await event_bus.stop()
    
    # Assertions
    assert len(captured_events) == 1
    plan_event = captured_events[0]
    
    assert plan_event.type == "ExecutionPlanGenerated"
    assert plan_event.payload["task_id"] == "task-planner-123"
    
    plan_data = plan_event.payload["plan"]
    assert len(plan_data["nodes"]) == 7
    
    # Check that TSLA symbol was extracted and injected
    node1 = next(n for n in plan_data["nodes"] if n["id"] == "node1")
    assert node1["parameters"].get("symbol") == "TSLA"
    
    # Check node 3 dependencies
    node3 = next(n for n in plan_data["nodes"] if n["id"] == "node3")
    assert "node1" in node3["dependencies"]
    assert "node2" in node3["dependencies"]
