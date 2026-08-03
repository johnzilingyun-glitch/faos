"""
Auto-persist completed tasks into SQLite history.

Event-driven, zero-intrusion: subscribes to ``TaskCompleted`` on the
EventBus, assembles a history record from the task's ExecutionContext
(same shape the frontend uses via ``POST /api/history``) and writes it
through :mod:`faos.services.history.storage` on a worker thread.

Tasks that produced no analysis output (e.g. pure backtest runs) are
skipped. A ``HistorySaved`` event is published on success so the
frontend / observability layer can react in real time.
"""
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from faos.core.models import Event

logger = logging.getLogger("faos.history.auto_persist")


class HistoryAutoPersistService:
    """Persist finished analysis tasks to the history store automatically."""

    def __init__(self, event_bus, contexts: Dict[str, Any], storage=None, active_tasks: Optional[Dict[str, Any]] = None):
        self.event_bus = event_bus
        self.contexts = contexts
        self.active_tasks = active_tasks or {}
        if storage is None:
            from faos.services.history import history_storage
            storage = history_storage
        self.storage = storage
        self.event_bus.subscribe("TaskCompleted", self._on_task_completed)
        logger.info("HistoryAutoPersistService subscribed to TaskCompleted")

    # ── Event handler ───────────────────────────────────────────────

    async def _on_task_completed(self, event: Event):
        task_id = event.payload.get("task_id")
        if not task_id:
            return
        context = self.contexts.get(task_id)
        if context is None:
            logger.warning(f"Auto-persist: no context for task {task_id}, skipping")
            return

        record = self.build_record(task_id, context)
        if record is None:
            logger.info(f"Auto-persist: task {task_id} has no report/decision output, skipping")
            return

        try:
            ok = await asyncio.to_thread(self.storage.save_record, record)
        except Exception as e:  # noqa: BLE001 — persistence must never break the task flow
            logger.error(f"Auto-persist failed for task {task_id}: {e}")
            return

        if ok:
            await self.event_bus.publish(Event(
                type="HistorySaved",
                source="HistoryAutoPersistService",
                payload={"task_id": task_id, "record_id": record["id"], "symbol": record["symbol"]},
            ))
            logger.info(f"Auto-persisted history record for task {task_id} ({record['symbol']})")

    # ── Record assembly ─────────────────────────────────────────────

    def build_record(self, task_id: str, context) -> Optional[Dict[str, Any]]:
        """Map an ExecutionContext into the frontend history record shape.

        Returns None when the task produced nothing worth archiving
        (no report and no decision — e.g. backtest bookkeeping tasks).
        """
        results = context.snapshot_results() if hasattr(context, "snapshot_results") else dict(context.results)
        provider_outputs = (
            context.snapshot_provider_outputs()
            if hasattr(context, "snapshot_provider_outputs")
            else dict(context.provider_outputs)
        )

        report = results.get("report") or ""
        decision = results.get("decision") or {}
        if not report and not decision:
            return None

        fact_sheet = getattr(context, "fact_sheet", None) or {}
        symbol = (
            fact_sheet.get("symbol")
            or (provider_outputs.get("quote") or {}).get("symbol")
            or "Asset"
        )

        intent = context.get_variable("intent", "") if hasattr(context, "get_variable") else ""
        chat_history = [{"role": "user", "content": intent}] if intent else []

        market_data: Dict[str, Any] = {}
        if provider_outputs.get("quote"):
            market_data["quote"] = provider_outputs["quote"]
        if fact_sheet:
            market_data["fact_sheet"] = fact_sheet

        return {
            # Reuse task_id as record id: INSERT OR REPLACE makes reruns
            # and a later manual frontend save for the same task idempotent.
            "id": task_id,
            "symbol": symbol,
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "chatHistory": chat_history,
            "followUpHistory": [],
            "reportContent": report if isinstance(report, str) else str(report),
            "decision": decision,
            "analysisReports": results.get("analysis_reports") or {},
            "discussion": results.get("discussion") or {},
            "marketData": market_data,
        }
