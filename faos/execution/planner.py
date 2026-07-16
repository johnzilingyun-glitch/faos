import logging
import json
from typing import Optional
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.event_bus import EventBus
from faos.services.workflow.service import WorkflowService
from faos.services.capability.service import CapabilityService
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.execution.planner_models import PlannerResponse

logger = logging.getLogger(__name__)

class PlannerPipeline:
    def __init__(self, event_bus: EventBus, workflow_service: WorkflowService = None, capability_service: CapabilityService = None, reasoning_service: ReasoningService = None):
        self.event_bus = event_bus
        self.workflow_service = workflow_service
        self.capability_service = capability_service
        self.reasoning_service = reasoning_service
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)
        
    async def _handle_task_submitted(self, event: Event):
        task_id = event.payload.get("task_id")
        intent = event.payload.get("intent", "")
        
        logger.info(f"Planner processing Task {task_id} with intent: {intent}")
        
        if not self.workflow_service or not self.reasoning_service:
            logger.error("WorkflowService or ReasoningService is not initialized in PlannerPipeline")
            return
            
        # Get all registered workflows to let LLM choose
        available_workflows = []
        for wf_id, wf_def in self.workflow_service.workflows.items():
            available_workflows.append({
                "id": wf_id,
                "name": getattr(wf_def, "name", wf_id),
                "description": getattr(wf_def, "description", "No description available")
            })
            
        system_prompt = (
            "You are the AI Planner (Orchestrator) for the FAOS Agentic System.\n"
            "Your job is to parse the user's intent, select the most appropriate Workflow ID, "
            "and extract required parameters.\n"
            "Respond strictly in valid JSON matching the following schema:\n"
            "{\n"
            '  "workflow_id": "string",\n'
            '  "parameters": {"key": "value"},\n'
            '  "reasoning": "string"\n'
            "}"
        )
        
        context_data = {
            "intent": intent,
            "available_workflows": available_workflows
        }
        
        req = ReasoningRequest(
            task_id=task_id,
            prompt=system_prompt,
            context_data=context_data,
            model="gemini-3.5-flash"  # Using fastest model for routing
        )
        
        resp = await self.reasoning_service.analyze_context(req)
        
        workflow_id = "AnalyzeStockWorkflow"  # Fallback
        params = {"symbol": "AAPL"}  # Fallback
        
        try:
            # Simple json extraction from LLM response
            raw_response = resp.raw_response
            start = raw_response.find("{")
            end = raw_response.rfind("}")
            if start != -1 and end != -1:
                json_str = raw_response[start:end+1]
                data = json.loads(json_str)
                validated_data = PlannerResponse(**data)
                workflow_id = validated_data.workflow_id
                params = validated_data.parameters
                logger.info(f"Planner AI Decision: Workflow={workflow_id}, Params={params}, Reasoning={validated_data.reasoning}")
        except Exception as e:
            logger.error(f"Planner failed to parse LLM response: {e}. Using fallback.")
            
        workflow_def = self.workflow_service.get_workflow(workflow_id)
        if not workflow_def:
            logger.warning(f"Workflow '{workflow_id}' not found, falling back to 'AnalyzeStockWorkflow'")
            workflow_id = "AnalyzeStockWorkflow"
            workflow_def = self.workflow_service.get_workflow(workflow_id)
            if not workflow_def:
                logger.error("Fallback Workflow 'AnalyzeStockWorkflow' not found.")
                return
            
        # 3. Execution Plan Generation
        plan_nodes = []
        for w_node in workflow_def.nodes:
            # Inject parameters into capabilities that need them dynamically
            node_params = {}
            if self.capability_service:
                capability = self.capability_service.get_capability(w_node.capability)
                if capability:
                    for required_input in capability.inputs:
                        if required_input in params:
                            node_params[required_input] = params[required_input]
                
            plan_nodes.append(PlanNode(
                id=w_node.id,
                capability=w_node.capability,
                parameters=node_params,
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
        logger.info(f"Planner generated ExecutionPlan for Task {task_id} using {workflow_id}")
