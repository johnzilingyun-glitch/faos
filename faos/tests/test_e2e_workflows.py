"""
End-to-end workflow tests (offline, deterministic).

Runs with Settings(env="mock") so no real network providers are registered
and the ReasoningService stays in mock mode — the full pipeline
(Planner -> DAG -> Skills -> Report) executes without any external API.
"""
import asyncio

import pytest

from faos.core.config import Settings
from faos.core.context import ExecutionContext
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.runtime import TaskRuntime


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        env="mock",
        node_timeout_seconds=60.0,
        node_max_retries=1,
        task_context_ttl_seconds=600.0,
    )


def test_capability_routing_is_coherent(mock_settings):
    """Every workflow node must route to a registered skill + catalog entry.

    Regression guard for the broken BacktestWorkflow link (nodes declared
    'InitBacktest'/'RunBacktestLoop' while skills registered 'cap.*').
    """
    runtime = TaskRuntime(settings=mock_settings)

    assert runtime.workflow_service.workflows, "no workflows registered"
    for wf_id, wf_def in runtime.workflow_service.workflows.items():
        for node in wf_def.nodes:
            assert runtime.skill_service.get_skill(node.capability) is not None, (
                f"workflow '{wf_id}' node '{node.id}' routes to unregistered "
                f"capability '{node.capability}'"
            )
            assert runtime.capability_service.get_capability(node.capability) is not None, (
                f"capability '{node.capability}' missing from catalog"
            )

    backtest = runtime.workflow_service.get_workflow("BacktestWorkflow")
    caps = [n.capability for n in backtest.nodes]
    assert "cap.init_backtest" in caps
    assert "cap.run_backtest_loop" in caps


@pytest.mark.asyncio
async def test_analyze_stock_workflow_end_to_end(mock_settings):
    """Full pipeline: intent -> planner -> DAG -> decision + report (all mock)."""
    runtime = TaskRuntime(settings=mock_settings)
    runtime.start()

    loop = asyncio.get_running_loop()
    completed = loop.create_future()

    async def on_completed(event: Event):
        if not completed.done():
            completed.set_result(event.payload.get("task_id"))

    runtime.event_bus.subscribe("TaskCompleted", on_completed)

    task = await runtime.submit_task("分析 AAPL", {"llm_config": {"provider": "mock"}})
    finished_id = await asyncio.wait_for(completed, timeout=90)
    assert finished_id == task.id

    ctx = runtime.get_context(task.id)
    assert ctx is not None
    assert ctx.provider_outputs.get("quote"), "quote data missing"
    assert ctx.provider_outputs.get("news"), "news data missing"
    assert "analysis_reports" in ctx.results
    assert "discussion" in ctx.results
    assert "decision" in ctx.results
    assert ctx.results["decision"]["action"] in ("BUY", "SELL", "HOLD")
    assert "report" in ctx.results

    await runtime.stop()


@pytest.mark.asyncio
async def test_backtest_workflow_nodes_execute(mock_settings):
    """Backtest init + loop skills execute through the DAG engine (no LLM needed)."""
    runtime = TaskRuntime(settings=mock_settings)
    runtime.start()

    task_id = "task-backtest-e2e"
    runtime.contexts[task_id] = ExecutionContext(task_id=task_id, variables={})

    loop = asyncio.get_running_loop()
    completed = loop.create_future()

    async def on_completed(event: Event):
        if event.payload.get("task_id") == task_id and not completed.done():
            completed.set_result(True)

    runtime.event_bus.subscribe("TaskCompleted", on_completed)

    plan = ExecutionPlan(
        task_id=task_id,
        nodes=[
            PlanNode(id="init_backtest", capability="cap.init_backtest",
                     parameters={"symbol": "TSLA"}),
            PlanNode(id="run_backtest_loop", capability="cap.run_backtest_loop",
                     dependencies=["init_backtest"], parameters={"symbol": "TSLA"}),
        ],
    )
    await runtime.event_bus.publish(Event(
        type="ExecutionPlanGenerated",
        source="Test",
        payload={"task_id": task_id, "plan": plan.model_dump()},
    ))

    await asyncio.wait_for(completed, timeout=30)
    assert "backtest_metrics" in runtime.contexts[task_id].results

    await runtime.stop()
