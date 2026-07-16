import pytest
import asyncio
from faos.core.event_bus import EventBus
from faos.core.models import Event
from faos.execution.planner import PlannerPipeline

@pytest.mark.asyncio
async def test_planner_pipeline_generates_plan():
    event_bus = EventBus()
    event_bus.start()
    
    # We need a way to capture events published by the planner
    captured_events = []
    
    async def capture_handler(event: Event):
        captured_events.append(event)
        
    event_bus.subscribe("ExecutionPlanGenerated", capture_handler)
    
    planner = PlannerPipeline(event_bus)
    
    # Simulate a task submission
    test_task_id = "test-task-123"
    task_event = Event(
        type="TaskSubmitted",
        source="Test",
        payload={"task_id": test_task_id, "intent": "Analyze AAPL"}
    )
    
    await event_bus.publish(task_event)
    
    # Allow time for event loop to process
    await asyncio.sleep(0.1)
    
    # Stop the event bus to flush
    await event_bus.stop()
    
    # Assertions
    assert len(captured_events) == 1
    plan_event = captured_events[0]
    
    assert plan_event.type == "ExecutionPlanGenerated"
    assert plan_event.payload["task_id"] == test_task_id
    
    plan_data = plan_event.payload["plan"]
    assert len(plan_data["nodes"]) == 4
    
    # Check node 3 dependencies
    node3 = next(n for n in plan_data["nodes"] if n["id"] == "node3")
    assert "node1" in node3["dependencies"]
    assert "node2" in node3["dependencies"]
