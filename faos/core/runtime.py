import asyncio
import logging
from typing import Dict, Optional, Set
from faos.core.config import Settings
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

    Service wiring lives in ``_register_default_services`` so tests and
    alternative bootstraps can subclass/replace individual pieces.
    Completed tasks and their contexts are reclaimed after
    ``settings.task_context_ttl_seconds`` to bound memory growth.
    """
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.event_bus = EventBus()
        self.active_tasks: Dict[str, Task] = {}
        self.contexts: Dict[str, ExecutionContext] = {}
        self._gc_tasks: Set[asyncio.Task] = set()

        from faos.services.observability.service import ObservabilityService
        self.observability = ObservabilityService(event_bus=self.event_bus)

        from faos.services.security.service import SecurityGovernanceService
        self.security_governance = SecurityGovernanceService()

        from faos.services.plugin.service import PluginService
        self.plugin_service = PluginService()

        from faos.services.knowledge.service import KnowledgeService
        self.knowledge_service = KnowledgeService()

        from faos.services.reasoning.service import ReasoningService
        self.reasoning = ReasoningService(event_bus=self.event_bus)

        self._register_default_services()

        # Instantiate Planner and Execution Engine
        self.planner = PlannerPipeline(
            self.event_bus,
            workflow_service=self.workflow_service,
            capability_service=self.capability_service,
            reasoning_service=self.reasoning
        )
        self.engine = ExecutionEngine(
            self.event_bus,
            self.contexts,
            skill_service=self.skill_service,
            node_timeout=self.settings.node_timeout_seconds,
            max_retries=self.settings.node_max_retries,
        )

        self._validate_capabilities()

        # Auto-persist finished analysis tasks into SQLite history
        # (event-driven; disable with FAOS_AUTO_PERSIST=0).
        self.history_auto_persist = None
        if self.settings.history_auto_persist:
            from faos.services.history.auto_persist import HistoryAutoPersistService
            self.history_auto_persist = HistoryAutoPersistService(
                event_bus=self.event_bus,
                contexts=self.contexts,
                active_tasks=self.active_tasks,
            )

        self._running = False

        # Subscribe to internal lifecycle events
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)
        self.event_bus.subscribe("TaskCompleted", self._handle_task_completed)
        self.event_bus.subscribe("TaskFailed", self._handle_task_failed)

        # Initialize CronManager
        from faos.core.cron import CronManager
        self.cron_manager = CronManager(self)

    # ── Service wiring ──────────────────────────────────────────────

    def _register_default_services(self):
        """Register all default services, skills, workflows and capabilities.

        Honour ``settings.is_mock_env`` (FAOS_ENV=mock): when set, real
        network providers (yfinance / web search) are skipped so runs are
        deterministic and offline-friendly.
        """
        from faos.services.skill.service import SkillService
        from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill, AnalyzeSkill, GenerateReportSkill, DecisionSkill
        from faos.services.provider.service import ProviderService
        from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider
        from faos.services.decision.service import DecisionService

        self.provider_service = ProviderService(security=self.security_governance)

        if not self.settings.is_mock_env:
            # Register real providers (Priority 100)
            from faos.services.provider.yfinance_impl import YFinanceQuoteProvider, YFinanceNewsProvider
            from faos.services.provider.websearch_impl import WebSearchProvider
            from faos.services.provider.a_stock_provider import AStockDirectProvider

            self.provider_service.register_provider(AStockDirectProvider())
            self.provider_service.register_provider(YFinanceQuoteProvider())
            self.provider_service.register_provider(YFinanceNewsProvider())
            self.provider_service.register_provider(WebSearchProvider())
        else:
            logger.info("FAOS_ENV=mock: skipping real network providers (yfinance/websearch)")

        # Register mock providers (Priority 10, always available as fallback)
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

        from faos.services.portfolio.service import PortfolioService
        self.portfolio_service = PortfolioService()
        self.skill_service.register_skill(DecisionSkill(decision_service=self.decision_service, portfolio_service=self.portfolio_service))

        from faos.services.reflection.service import ReflectionService
        from faos.services.skill.impl import ReflectionSkill
        from faos.services.skill.backtest_skill import BacktestInitSkill, BacktestLoopSkill

        self.reflection_service = ReflectionService(self.reasoning)
        self.skill_service.register_skill(ReflectionSkill(reflection_service=self.reflection_service))
        self.skill_service.register_skill(BacktestInitSkill(event_bus=self.event_bus))
        self.skill_service.register_skill(BacktestLoopSkill(event_bus=self.event_bus))

        from faos.services.report.service import ReportService
        self.report_service = ReportService()
        self.skill_service.register_skill(GenerateReportSkill(report_service=self.report_service))

        from faos.services.skill.sector_scan import SectorScanSkill, BatchFetchDataSkill, CompareStocksSkill
        self.skill_service.register_skill(SectorScanSkill(reasoning_service=self.reasoning))
        self.skill_service.register_skill(BatchFetchDataSkill(data_route=self.data_route))
        self.skill_service.register_skill(CompareStocksSkill(reasoning_service=self.reasoning))

        from faos.services.workflow.service import WorkflowService
        from faos.services.workflow.standard import (
            get_analyze_stock_workflow,
            get_news_summary_workflow,
            get_backtest_workflow,
            get_sector_scan_workflow
        )

        self.workflow_service = WorkflowService()
        self.workflow_service.register_workflow(get_analyze_stock_workflow())
        self.workflow_service.register_workflow(get_news_summary_workflow())
        self.workflow_service.register_workflow(get_backtest_workflow())
        self.workflow_service.register_workflow(get_sector_scan_workflow())

        # Capability catalog mirrors the Skill registry (single source of truth).
        from faos.services.capability.service import CapabilityService
        self.capability_service = CapabilityService()
        for skill in self.skill_service.skills_by_capability.values():
            self.capability_service.register_from_skill(skill.manifest)

        # Capability knowledge items (used by Knowledge queries / MCP discovery)
        from faos.services.knowledge.models import KnowledgeItem, KnowledgeCategory
        for cap_id, skill in sorted(self.skill_service.skills_by_capability.items()):
            self.knowledge_service.register_item(KnowledgeItem(
                id=cap_id,
                name=skill.manifest.name,
                category=KnowledgeCategory.CAPABILITY,
                description=skill.manifest.description or skill.manifest.name,
                metadata={"related_skills": [skill.manifest.id]},
            ))

    def _validate_capabilities(self):
        """Fail fast if any workflow node routes to an unregistered capability."""
        problems = []
        for wf_id, wf_def in self.workflow_service.workflows.items():
            for node in wf_def.nodes:
                if self.skill_service.get_skill(node.capability) is None:
                    problems.append(f"workflow '{wf_id}' node '{node.id}' -> capability '{node.capability}' has no registered skill")
                if self.capability_service.get_capability(node.capability) is None:
                    problems.append(f"workflow '{wf_id}' node '{node.id}' -> capability '{node.capability}' missing from capability catalog")
        if problems:
            raise RuntimeError(
                "Capability routing validation failed:\n  - " + "\n  - ".join(problems)
            )
        logger.info("Capability routing validation passed "
                    f"({len(self.workflow_service.workflows)} workflows, "
                    f"{len(self.skill_service.skills_by_capability)} skills)")

    # ── Lifecycle ───────────────────────────────────────────────────

    def start(self):
        """Start the Task Runtime and its components."""
        if not self._running:
            self._running = True
            self.event_bus.start()
            if hasattr(self, 'cron_manager'):
                self.cron_manager.start()
            logger.info("TaskRuntime started")

    async def stop(self):
        """Stop the Task Runtime."""
        if self._running:
            self._running = False
            for task in list(self._gc_tasks):
                task.cancel()
            if self._gc_tasks:
                await asyncio.gather(*self._gc_tasks, return_exceptions=True)
            if hasattr(self, 'cron_manager'):
                self.cron_manager.stop()
            await self.event_bus.stop()
            logger.info("TaskRuntime stopped")

    async def submit_task(self, intent: str, initial_context: Optional[Dict] = None) -> Task:
        """Entry point for users to submit a new Task."""
        task = Task(intent=intent, context=initial_context or {})
        self.active_tasks[task.id] = task
        self._evict_finished_tasks_if_needed()

        # Initialize ExecutionContext with the initial_context variables (like llm_config)
        context_vars = initial_context.copy() if initial_context else {}
        context_vars["intent"] = intent
        self.contexts[task.id] = ExecutionContext(task_id=task.id, variables=context_vars)

        # Publish TaskSubmitted event to trigger Planner Pipeline
        event = Event(
            type="TaskSubmitted",
            source="TaskRuntime",
            payload={
                "task_id": task.id,
                "intent": intent,
                "llm_config": context_vars.get("llm_config")
            }
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
        self._schedule_reclaim(task_id)

    async def _handle_task_failed(self, event: Event):
        task_id = event.payload.get("task_id")
        if task_id in self.active_tasks:
            self.active_tasks[task_id].status = "failed"
            error_msg = event.payload.get("error", "Unknown error")
            logger.error(f"Task {task_id} failed: {error_msg}")
        self._schedule_reclaim(task_id)

    # ── Memory hygiene ──────────────────────────────────────────────

    def _schedule_reclaim(self, task_id: str):
        """Reclaim task record + execution context after the configured TTL."""
        async def _gc():
            try:
                await asyncio.sleep(self.settings.task_context_ttl_seconds)
                self.contexts.pop(task_id, None)
                self.active_tasks.pop(task_id, None)
                logger.debug(f"Reclaimed task {task_id} (context + record)")
            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(_gc())
        self._gc_tasks.add(task)
        task.add_done_callback(self._gc_tasks.discard)

    def _evict_finished_tasks_if_needed(self):
        """Hard cap on retained tasks; evict oldest finished entries first."""
        overflow = len(self.active_tasks) - self.settings.max_active_tasks
        if overflow <= 0:
            return
        finished = [tid for tid, t in self.active_tasks.items() if t.status in ("completed", "failed")]
        for tid in finished[:overflow]:
            self.active_tasks.pop(tid, None)
            self.contexts.pop(tid, None)

    def get_context(self, task_id: str) -> Optional[ExecutionContext]:
        """Retrieve the shared ExecutionContext for a specific Task."""
        return self.contexts.get(task_id)


def create_runtime(settings: Optional[Settings] = None) -> TaskRuntime:
    """Composition-root factory: build a fully wired TaskRuntime."""
    return TaskRuntime(settings=settings)
