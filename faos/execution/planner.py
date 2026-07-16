import logging
import re
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.event_bus import EventBus
from faos.services.workflow.service import WorkflowService
from faos.services.capability.service import CapabilityService

logger = logging.getLogger(__name__)

class PlannerPipeline:
    def __init__(self, event_bus: EventBus, workflow_service: WorkflowService = None, capability_service: CapabilityService = None):
        self.event_bus = event_bus
        self.workflow_service = workflow_service
        self.capability_service = capability_service
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)
        
    async def _handle_task_submitted(self, event: Event):
        task_id = event.payload.get("task_id")
        intent = event.payload.get("intent", "")
        
        logger.info(f"Planner processing Task {task_id} with intent: {intent}")
        
        if not self.workflow_service:
            logger.error("WorkflowService is not initialized in PlannerPipeline")
            return
            
        # 1. Intent Parsing (Mock logic for Phase 6)
        # Extract symbol from intent like "Analyze AAPL" or default to AAPL
        symbol = "AAPL"
        match = re.search(r"Analyze\s+([A-Za-z]+)", intent, re.IGNORECASE)
        if match:
            symbol = match.group(1).upper()
            
        # 2. Workflow Discovery (Mock static selection for Phase 6)
        workflow_id = "AnalyzeStockWorkflow"
        workflow_def = self.workflow_service.get_workflow(workflow_id)
        
        if not workflow_def:
            logger.error(f"Workflow '{workflow_id}' not found in WorkflowService")
            return
            
        # 3. Execution Plan Generation
        # Convert WorkflowNodeDefs to PlanNodes, injecting parameters
        plan_nodes = []
        for w_node in workflow_def.nodes:
            # Inject symbol into capabilities that need it dynamically
            params = {}
            if self.capability_service:
                capability = self.capability_service.get_capability(w_node.capability)
                if capability and "symbol" in capability.inputs:
                    params["symbol"] = symbol
                
            plan_nodes.append(PlanNode(
                id=w_node.id,
                capability=w_node.capability,
                parameters=params,
                dependencies=w_node.dependencies
            ))
            
        plan = ExecutionPlan(
            task_id=task_id,
            nodes=plan_nodes
        )
        
        plan_event = Event(
            type="ExecutionPlanGenerated",
            source="PlannerPipeline",
            payload={"task_id": task_id, "plan": plan.model_dump()}
        )
        
        await self.event_bus.publish(plan_event)
        logger.info(f"Planner generated ExecutionPlan for Task {task_id} using {workflow_id} (symbol: {symbol})")
