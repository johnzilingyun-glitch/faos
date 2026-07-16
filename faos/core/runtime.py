import asyncio
import logging
from typing import Dict, Optional
from faos.core.models import Task, Event
from faos.core.event_bus import EventBus
from faos.core.context import ExecutionContext
from faos.execution.planner import PlannerPipeline
from faos.execution.engine import ExecutionEngine

logger = logging.getLogger(__name__)

class TaskRuntime:
    """
    The only runtime in the FAOS system.
    Responsible for:
    - Task Lifecycle
    - Task Queue
    - Event Dispatch
    - Execution Context management
    """
    def __init__(self):
        self.event_bus = EventBus()
        self.active_tasks: Dict[str, Task] = {}
        self.contexts: Dict[str, ExecutionContext] = {}
        
        from faos.services.reasoning.service import ReasoningService
        self.reasoning = ReasoningService()
        
        from faos.services.skill.service import SkillService
        from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill, AnalyzeSkill, GenerateReportSkill
        from faos.services.provider.service import ProviderService
        from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider
        
        self.provider_service = ProviderService()
        self.provider_service.register_provider(MockQuoteProvider())
        self.provider_service.register_provider(MockNewsProvider())
        
        self.skill_service = SkillService()
        self.skill_service.register_skill(FetchDataSkill(provider_service=self.provider_service))
        self.skill_service.register_skill(FetchNewsSkill(provider_service=self.provider_service))
        self.skill_service.register_skill(AnalyzeSkill(reasoning_service=self.reasoning))
        self.skill_service.register_skill(GenerateReportSkill())
        
        from faos.services.workflow.service import WorkflowService
        from faos.services.workflow.standard import get_analyze_stock_workflow
        
        self.workflow_service = WorkflowService()
        self.workflow_service.register_workflow(get_analyze_stock_workflow())
        
        # Instantiate Planner and Execution Engine
        self.planner = PlannerPipeline(self.event_bus, workflow_service=self.workflow_service)
        self.engine = ExecutionEngine(self.event_bus, self.contexts, skill_service=self.skill_service)
        
        self._running = False
        
        # Subscribe to internal lifecycle events
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)
        self.event_bus.subscribe("TaskCompleted", self._handle_task_completed)
        self.event_bus.subscribe("TaskFailed", self._handle_task_failed)

    def start(self):
        """Start the Task Runtime and its components."""
        if not self._running:
            self._running = True
            self.event_bus.start()
            logger.info("TaskRuntime started")

    async def stop(self):
        """Stop the Task Runtime."""
        if self._running:
            self._running = False
            await self.event_bus.stop()
            logger.info("TaskRuntime stopped")

    async def submit_task(self, intent: str, initial_context: Optional[Dict] = None) -> Task:
        """Entry point for users to submit a new Task."""
        task = Task(intent=intent, context=initial_context or {})
        self.active_tasks[task.id] = task
        self.contexts[task.id] = ExecutionContext(task_id=task.id)
        
        # Publish TaskSubmitted event to trigger Planner Pipeline
        event = Event(
            type="TaskSubmitted",
            source="TaskRuntime",
            payload={"task_id": task.id, "intent": intent}
        )
        await self.event_bus.publish(event)
        return task

    async def _handle_task_submitted(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = "running"
            logger.info(f"Task {task_id} transitioned to running")

    async def _handle_task_completed(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = "completed"
            logger.info(f"Task {task_id} completed successfully")
            
    async def _handle_task_failed(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = "failed"
            error_msg = event.payload.get("error", "Unknown error")
            logger.error(f"Task {task_id} failed: {error_msg}")
            
    def get_context(self, task_id: str) -> Optional[ExecutionContext]:
        """Retrieve the shared ExecutionContext for a specific Task."""
        return self.contexts.get(task_id)
