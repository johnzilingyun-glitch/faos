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
        
        from faos.services.observability.service import ObservabilityService
        self.observability = ObservabilityService(event_bus=self.event_bus)

        
        from faos.services.plugin.service import PluginService
        self.plugin_service = PluginService()
        
        from faos.services.knowledge.service import KnowledgeService
        from faos.services.knowledge.models import KnowledgeItem, KnowledgeCategory
        
        self.knowledge_service = KnowledgeService()
        
        # Register base Capability Knowledge
        self.knowledge_service.register_item(KnowledgeItem(
            id="capability.fetch_data",
            name="Fetch Market Data",
            category=KnowledgeCategory.CAPABILITY,
            description="Fetch stock quotes and price information",
            metadata={"related_skills": ["FetchDataSkill"]}
        ))
        
        self.knowledge_service.register_item(KnowledgeItem(
            id="capability.fetch_news",
            name="Fetch Market News",
            category=KnowledgeCategory.CAPABILITY,
            description="Fetch recent news articles and sentiment for an entity",
            metadata={"related_skills": ["FetchNewsSkill"]}
        ))
        
        self.knowledge_service.register_item(KnowledgeItem(
            id="capability.analyze",
            name="Analyze Entity",
            category=KnowledgeCategory.CAPABILITY,
            description="Analyze financial metrics and market sentiment",
            metadata={"related_skills": ["AnalyzeSkill"]}
        ))
        
        
        import os
        faos_env = os.environ.get("FAOS_ENV", "mock").lower()
        
        from faos.services.reasoning.service import ReasoningService
        self.reasoning = ReasoningService()
        
        from faos.services.skill.service import SkillService
        from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill, AnalyzeSkill, GenerateReportSkill, DecisionSkill
        from faos.services.provider.service import ProviderService
        from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider
        from faos.services.decision.service import DecisionService
        
        self.provider_service = ProviderService()
        
        # Register real providers (Priority 100)
        from faos.services.provider.yfinance_impl import YFinanceQuoteProvider, YFinanceNewsProvider
        self.provider_service.register_provider(YFinanceQuoteProvider())
        self.provider_service.register_provider(YFinanceNewsProvider())
        
        # Register mock providers (Priority 10)
        self.provider_service.register_provider(MockQuoteProvider())
        self.provider_service.register_provider(MockNewsProvider())
        
        from faos.services.data_route.service import DataRouteService
        self.data_route = DataRouteService(self.provider_service)
        
        self.decision_service = DecisionService(self.reasoning)
        from faos.services.discussion.service import DiscussionService
        self.discussion_service = DiscussionService(self.reasoning)
        
        from faos.services.analyze.service import AnalyzeService
        self.analyze_service = AnalyzeService(self.reasoning)
        
        self.skill_service = SkillService()
        self.skill_service.register_skill(FetchDataSkill(data_route=self.data_route))
        self.skill_service.register_skill(FetchNewsSkill(data_route=self.data_route))
        self.skill_service.register_skill(AnalyzeSkill(analyze_service=self.analyze_service))
        
        from faos.services.skill.impl import DiscussSkill
        self.skill_service.register_skill(DiscussSkill(discussion_service=self.discussion_service))
        
        self.skill_service.register_skill(DecisionSkill(decision_service=self.decision_service))
        
        from faos.services.reflection.service import ReflectionService
        from faos.services.skill.impl import ReflectionSkill
        self.reflection_service = ReflectionService(self.reasoning)
        self.skill_service.register_skill(ReflectionSkill(reflection_service=self.reflection_service))
        
        from faos.services.report.service import ReportService
        self.report_service = ReportService()
        self.skill_service.register_skill(GenerateReportSkill(report_service=self.report_service))
        
        from faos.services.workflow.service import WorkflowService
        from faos.services.workflow.standard import get_analyze_stock_workflow
        
        self.workflow_service = WorkflowService()
        self.workflow_service.register_workflow(get_analyze_stock_workflow())
        
        from faos.services.capability.service import CapabilityService
        from faos.services.capability.models import CapabilityManifest
        
        self.capability_service = CapabilityService()
        self.capability_service.register_capability(CapabilityManifest(id="cap.fetch_data", name="FetchData", inputs=["symbol"]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.fetch_news", name="FetchNews", inputs=["symbol"]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.analyze", name="Analyze", inputs=[]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.discuss", name="Discussion", inputs=[]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.decision", name="Decision", inputs=[]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.reflection", name="Reflection", inputs=[]))
        self.capability_service.register_capability(CapabilityManifest(id="cap.report", name="GenerateReport", inputs=[]))
        
        # Instantiate Planner and Execution Engine
        self.planner = PlannerPipeline(
            self.event_bus, 
            workflow_service=self.workflow_service,
            capability_service=self.capability_service
        )
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
        
        # Initialize ExecutionContext with the initial_context variables (like llm_config)
        context_vars = initial_context.copy() if initial_context else {}
        self.contexts[task.id] = ExecutionContext(task_id=task.id, variables=context_vars)
        
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
