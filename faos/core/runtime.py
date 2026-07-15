import asyncio
import logging
from typing import Dict, Optional
from faos.core.models import Task, Event
from faos.core.event_bus import EventBus
from faos.core.context import ExecutionContext

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
