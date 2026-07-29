import pytest
import asyncio
from faos.core.event_bus import EventBus
from faos.core.context import ExecutionContext
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.execution.engine import ExecutionEngine
from faos.services.reasoning.service import ReasoningService
from faos.services.skill.service import SkillService
from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill, AnalyzeSkill, GenerateReportSkill, DecisionSkill
from faos.services.provider.service import ProviderService
from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider
from faos.services.decision.service import DecisionService

@pytest.mark.asyncio
async def test_engine_dag_execution():
    event_bus = EventBus()
    event_bus.start()

    contexts = {}
    task_id = "task-test-123"
    
    contexts[task_id] = ExecutionContext(task_id=task_id)
    
    reasoning_service = ReasoningService()
    
    provider_service = ProviderService()
    provider_service.register_provider(MockQuoteProvider())
    provider_service.register_provider(MockNewsProvider())
    
    from faos.services.data_route.service import DataRouteService
    data_route = DataRouteService(provider_service)

    from faos.services.discussion.service import DiscussionService
    discussion_service = DiscussionService(reasoning_service)

    from faos.services.analyze.service import AnalyzeService
    analyze_service = AnalyzeService(reasoning_service)
    
    from faos.services.decision.service import DecisionService
    decision_service = DecisionService(reasoning_service)
    
    from faos.services.report.service import ReportService
    report_service = ReportService()
    
    from faos.services.skill.impl import DiscussSkill
    
    skill_service = SkillService()
    skill_service.register_skill(FetchDataSkill(data_route=data_route))
    skill_service.register_skill(FetchNewsSkill(data_route=data_route))
    skill_service.register_skill(AnalyzeSkill(analyze_service=analyze_service))
    skill_service.register_skill(DiscussSkill(discussion_service=discussion_service))
    skill_service.register_skill(DecisionSkill(decision_service=decision_service))
    skill_service.register_skill(GenerateReportSkill(report_service=report_service))

    engine = ExecutionEngine(event_bus, contexts, skill_service=skill_service)

    # Capture events to verify event flow
    captured_events = []
    async def capture_handler(event: Event):
        captured_events.append(event)
    event_bus.subscribe("*", capture_handler)

    # A simple DAG:
    # node1 (FetchData)
    #   \
    #    node3 (Analyze)
    #   /
    # node2 (FetchNews)
    plan = ExecutionPlan(
        task_id=task_id,
        nodes=[
            PlanNode(id="node1", capability="cap.fetch_data", parameters={"symbol": "MSFT"}),
            PlanNode(id="node2", capability="cap.fetch_news", parameters={"symbol": "MSFT"}),
            PlanNode(id="node3", capability="cap.analyze", dependencies=["node1", "node2"]),
            PlanNode(id="node-discuss", capability="cap.discuss", dependencies=["node3"]),
            PlanNode(id="node4", capability="cap.decision", dependencies=["node-discuss"]),
            PlanNode(id="node5", capability="cap.report", dependencies=["node4"])
        ]
    )

    # Trigger via EventBus (ExecutionPlanGenerated)
    plan_event = Event(
        type="ExecutionPlanGenerated",
        source="Test",
        payload={"task_id": task_id, "plan": plan.model_dump()}
    )
    await event_bus.publish(plan_event)

    # Wait for execution:
    # FetchData and FetchNews take 0.5s (parallel = 0.5s)
    # Analyze takes 1.0s
    # Total ~2.0s. Let's wait 8.0s.
    await asyncio.sleep(8.0)
    await event_bus.stop()

    # Verify context changes
    context = contexts[task_id]
    # 4. Verify results
    assert "quote" in context.provider_outputs
    assert "news" in context.provider_outputs
    assert "analysis_reports" in context.results
    assert "discussion" in context.results
    assert "decision" in context.results
    
    assert context.provider_outputs["quote"]["symbol"] == "MSFT"
    assert context.results["decision"]["action"] in ["BUY", "SELL", "HOLD"]

    # Verify Event Flow
    event_types = [e.type for e in captured_events]
    assert "ExecutionStarted" in event_types
    assert "NodeStarted" in event_types
    assert "NodeCompleted" in event_types
    assert "TaskCompleted" in event_types

@pytest.mark.asyncio
async def test_engine_cycle_detection():
    event_bus = EventBus()
    event_bus.start()

    contexts = {}
    task_id = "task-test-456"
    contexts[task_id] = ExecutionContext(task_id=task_id)

    skill_service = SkillService()
    engine = ExecutionEngine(event_bus, contexts, skill_service=skill_service)

    captured_events = []
    async def capture_handler(event: Event):
        captured_events.append(event)
    event_bus.subscribe("TaskFailed", capture_handler)

    # Cyclic DAG: node1 depends on node2, node2 depends on node1
    plan = ExecutionPlan(
        task_id=task_id,
        nodes=[
            PlanNode(id="node1", capability="cap.fetch_data", dependencies=["node2"]),
            PlanNode(id="node2", capability="cap.fetch_news", dependencies=["node1"])
        ]
    )

    plan_event = Event(
        type="ExecutionPlanGenerated",
        source="Test",
        payload={"task_id": task_id, "plan": plan.model_dump()}
    )
    await event_bus.publish(plan_event)

    await asyncio.sleep(0.5)
    await event_bus.stop()

    # The task should fail with cycle detection error
    assert len(captured_events) == 1
    assert captured_events[0].type == "TaskFailed"
    assert "Cycle detected" in captured_events[0].payload["error"]
