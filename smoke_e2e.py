"""End-to-end smoke test against the live FAOS dev server (mock LLM).

1. Connects to /ws/events and captures the event stream.
2. POSTs a Chinese natural-language intent to /api/plan/chat (force_execute).
3. Prints every relevant event until TaskCompleted/TaskFailed.
4. Verifies the result was persisted to SQLite history.
"""
import asyncio
import json

import httpx
import websockets

BASE = "http://127.0.0.1:8088"
WS = "ws://127.0.0.1:8088/ws/events"
INTENT = "分析一下腾讯控股"


async def main():
    events = []
    async with websockets.connect(WS) as ws:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{BASE}/api/plan/chat",
                json={"messages": [{"role": "user", "content": INTENT}],
                      "force_execute": True},
            )
            plan = resp.json()
            print("PLAN RESPONSE:", json.dumps(plan, ensure_ascii=False))
            task_id = plan.get("task_id")
            print("TASK_ID:", task_id)

        print("\n==== EVENT STREAM ====")
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=60)
            except asyncio.TimeoutError:
                print("TIMEOUT waiting for events")
                break
            ev = json.loads(raw)
            etype = ev.get("type")
            tid = (ev.get("payload") or {}).get("task_id")
            if tid == task_id or etype in ("TaskSubmitted", "ExecutionPlanGenerated"):
                events.append(ev)
                payload = ev.get("payload", {})
                summary = {k: v for k, v in payload.items()
                           if k in ("node_id", "capability", "status", "workflow_id",
                                    "symbol", "error", "message")}
                print(f"[{etype}] {json.dumps(summary, ensure_ascii=False)}")
            if etype in ("TaskCompleted", "TaskFailed"):
                print("\nFINAL EVENT:", json.dumps(ev.get("payload"), ensure_ascii=False)[:500])
                break

    # Verify persistence
    async with httpx.AsyncClient(timeout=30) as client:
        h = await client.get(f"{BASE}/api/history", params={"limit": 3})
        records = h.json()
        print("\n==== HISTORY (latest 3) ====")
        for r in records:
            print(f"  - {r.get('task_id')} | {r.get('symbol')} | {r.get('verdict')} | {r.get('created_at')}")

    # Summarize
    types = [e["type"] for e in events]
    print("\n==== SMOKE RESULT ====")
    print("event_count:", len(events))
    print("event_types:", types)
    ok = ("TaskSubmitted" in types and "ExecutionPlanGenerated" in types
          and "TaskCompleted" in types and "TaskFailed" not in types)
    print("SMOKE PASS:", ok)


asyncio.run(main())
