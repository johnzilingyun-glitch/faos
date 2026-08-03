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
        # Keep tests from writing into the real faos_history.db;
        # auto-persist has its own dedicated test with a temp DB.
        history_auto_persist=False,
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


@pytest.mark.asyncio
async def test_auto_persist_writes_history_on_completion(tmp_path):
    """TaskCompleted should auto-save a history record (isolated temp DB)."""
    from faos.services.history.storage import HistoryStorage
    from faos.services.history.auto_persist import HistoryAutoPersistService

    settings = Settings(
        env="mock",
        node_timeout_seconds=60.0,
        node_max_retries=1,
        task_context_ttl_seconds=600.0,
        history_auto_persist=False,  # wire manually with the temp storage
    )
    runtime = TaskRuntime(settings=settings)
    storage = HistoryStorage(db_path=str(tmp_path / "history_test.db"))
    persister = HistoryAutoPersistService(
        event_bus=runtime.event_bus,
        contexts=runtime.contexts,
        storage=storage,
        active_tasks=runtime.active_tasks,
    )
    runtime.start()

    loop = asyncio.get_running_loop()
    saved = loop.create_future()

    async def on_saved(event: Event):
        if not saved.done():
            saved.set_result(event.payload)

    runtime.event_bus.subscribe("HistorySaved", on_saved)

    task = await runtime.submit_task("分析 AAPL", {"llm_config": {"provider": "mock"}})
    payload = await asyncio.wait_for(saved, timeout=90)

    assert payload["task_id"] == task.id
    assert payload["record_id"] == task.id

    records = storage.list_records()
    assert len(records) == 1
    rec = records[0]
    assert rec["id"] == task.id
    assert rec["symbol"] == payload["symbol"]
    assert rec["reportContent"], "report content should be persisted"
    assert rec["decision"] and rec["decision"]["action"] in ("BUY", "SELL", "HOLD")
    assert rec["analysisReports"], "analysis reports should be persisted"
    assert rec["chatHistory"] and rec["chatHistory"][0]["content"] == "分析 AAPL"

    # Backtest-style contexts (no report/decision) must be skipped.
    assert persister.build_record("no-output", ExecutionContext(task_id="no-output")) is None

    await runtime.stop()
