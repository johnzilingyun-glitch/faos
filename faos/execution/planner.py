import logging
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.event_bus import EventBus

logger = logging.getLogger(__name__)

class PlannerPipeline:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)
        
    async def _handle_task_submitted(self, event: Event):
        task_id = event.payload.get("task_id")
        intent = event.payload.get("intent")
        
        logger.info(f"Planner processing Task {task_id} with intent: {intent}")
        
        # Here we would normally call the ReasoningService (LLM) to generate a plan.
        # For Phase 3 MVP, we use a Mock strategy to return a fixed DAG.
        
        # Mock DAG:
        # node1 (FetchData)
        #   \
        #    node3 (Analyze) -> node4 (GenerateReport)
        #   /
        # node2 (FetchNews)
        
        plan = ExecutionPlan(
            task_id=task_id,
            nodes=[
                PlanNode(id="node1", capability="FetchData", parameters={"symbol": "AAPL"}),
                PlanNode(id="node2", capability="FetchNews", parameters={"symbol": "AAPL"}),
                PlanNode(id="node3", capability="Analyze", dependencies=["node1", "node2"]),
                PlanNode(id="node4", capability="GenerateReport", dependencies=["node3"])
            ]
        )
        
        plan_event = Event(
            type="ExecutionPlanGenerated",
            source="PlannerPipeline",
            payload={"task_id": task_id, "plan": plan.model_dump()}
        )
        
        await self.event_bus.publish(plan_event)
        logger.info(f"Planner generated ExecutionPlan for Task {task_id}")
