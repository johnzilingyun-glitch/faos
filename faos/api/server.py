import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from faos.core.runtime import TaskRuntime
from faos.core.models import Event
from faos.services.history import history_storage
from faos.services.backtest.accuracy import accuracy_backtester
from faos.services.reflection.experience import experience_service
from faos.services.portfolio import watchlist_service

logger = logging.getLogger("faos.api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="FAOS API")

# Global runtime instance (composition root)
runtime = TaskRuntime()
settings = runtime.settings

# CORS is locked down to the configured origin allowlist (FAOS_CORS_ORIGINS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_guard(request: Request, call_next):
    """Optional API-key guard.

    When FAOS_API_KEY is set, every /api/* request must present the same
    value in the X-API-Key header. When unset (local dev default), the API
    stays open. WebSocket auth is handled in the WS endpoint itself.
    """
    if settings.api_key and request.url.path.startswith("/api"):
        if request.headers.get("x-api-key") != settings.api_key:
            return JSONResponse({"detail": "Unauthorized: invalid or missing X-API-Key"}, status_code=401)
    return await call_next(request)


# WebSocket connections: {ws: task_filter}. task_filter=None means "all events"
# (backward compatible default); clients may narrow their stream by sending
# {"type": "subscribe", "task_id": "..."} / {"type": "unsubscribe"}.
active_websockets: Dict[WebSocket, Optional[str]] = {}

class TaskRequest(BaseModel):
    intent: str
    context: Dict[str, Any] = {}

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class PlannerChatRequest(BaseModel):
    messages: List[ChatMessage]
    force_execute: bool = False
    llm_config: Optional[Dict[str, Any]] = None

class ReportFollowupRequest(BaseModel):
    question: str
    symbol: Optional[str] = None
    report_content: Optional[str] = None
    conversation: List[ChatMessage] = []
    llm_config: Optional[Dict[str, Any]] = None

async def broadcast_event(event: Event):
    """Broadcasts an event to connected WebSockets, honouring per-client task filters."""
    event_dict = event.model_dump()
    # Convert datetime to string for JSON serialization
    event_dict['timestamp'] = event_dict['timestamp'].isoformat()
    message = json.dumps(event_dict)
    event_task_id = (event.payload or {}).get("task_id")

    for ws, task_filter in list(active_websockets.items()):
        # Scoped clients only receive events for their task (plus task-less global events).
        if task_filter is not None and event_task_id is not None and event_task_id != task_filter:
            continue
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to websocket: {e}")
            active_websockets.pop(ws, None)

@app.on_event("startup")
async def startup_event():
    runtime.start()

    # Subscribe the WebSocket broadcaster to all events
    runtime.event_bus.subscribe("*", broadcast_event)

    # Start background price refresh (every 10 minutes)
    watchlist_service.start_background_refresh()

    if settings.api_key:
        logger.info("FAOS API key guard ENABLED (FAOS_API_KEY is set)")
    logger.info(f"FAOS API Server started (env={settings.env}, cors={settings.cors_origins})")

@app.on_event("shutdown")
async def shutdown_event():
    await runtime.stop()

@app.post("/api/tasks")
async def submit_task(req: TaskRequest):
    task = await runtime.submit_task(req.intent, req.context)
    return {"task_id": task.id, "status": "submitted"}

@app.post("/api/plan/chat")
async def planner_chat(req: PlannerChatRequest):
    """
    Conversational Planner endpoint.

    Sends the conversation history to the Planner LLM.
    - If the Planner needs more info, it returns status='clarify' with a question.
    - If the Planner has enough info (or force_execute=True), it returns status='ready'
      and automatically submits the task to the runtime pipeline.
    """
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    result = await runtime.planner.chat(
        messages=messages,
        force=req.force_execute,
        llm_config=req.llm_config
    )

    response = {
        "status": result.status,
        "message": result.message,
        "workflow_id": result.workflow_id,
        "parameters": result.parameters,
    }

    # If ready, automatically submit the task to the runtime
    if result.status == "ready" and result.workflow_id:
        # Reconstruct the full intent from the last user message
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break

        context = {
            "llm_config": req.llm_config or {},
            "planner_params": result.parameters,
        }
        task = await runtime.submit_task(last_user_msg, context)
        response["task_id"] = task.id

    return response

@app.post("/api/report/followup")
async def report_followup(req: ReportFollowupRequest):
    """
    Answers a follow-up question about the CURRENT analysis in-context.

    This does NOT trigger a new workflow/pipeline. It uses the reasoning
    service to answer the user's question grounded strictly in the existing
    report and the prior follow-up conversation, so the user stays on the
    same analysis view.
    """
    from faos.services.reasoning.models import ReasoningRequest

    symbol = req.symbol or "Asset"
    lang = "zh"
    if req.llm_config and req.llm_config.get("language"):
        lang = req.llm_config["language"]

    # Format prior conversation for context
    convo_lines = []
    for m in req.conversation:
        speaker = "用户" if m.role == "user" else "助手"
        convo_lines.append(f"{speaker}: {m.content}")
    conversation_text = "\n".join(convo_lines) if convo_lines else "(暂无历史追问)"

    system_prompt = (
        "You are a senior investment research analyst acting as an interactive assistant. "
        "The user has already received a full analysis report for an asset and is now asking "
        "follow-up questions about it. Answer the user's question directly and specifically, "
        "grounded ONLY in the provided research report and the prior conversation. "
        "Do NOT start a new analysis or ask to run a workflow. If the report lacks the needed "
        "information, say so briefly and give your best reasoned judgment based on what is available. "
        "Keep the answer focused and well-structured."
    )

    context_data = {
        "user_parameters": {"language": lang, "symbol": symbol},
        "analysis_report": req.report_content or "(报告内容缺失)",
        "conversation_history": conversation_text,
        "question": req.question,
    }

    reasoning_req = ReasoningRequest(
        task_id=f"followup_{symbol}",
        context_data=context_data,
        prompt=system_prompt,
        llm_config=req.llm_config,
    )

    resp = await runtime.reasoning.analyze_context(reasoning_req)
    return {"answer": resp.raw_response or "抱歉，暂时无法生成回答。"}

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    # Optional WS auth: same key via header (browsers can use ?api_key=).
    if settings.api_key:
        key = websocket.headers.get("x-api-key") or websocket.query_params.get("api_key")
        if key != settings.api_key:
            await websocket.close(code=4401)
            return
    await websocket.accept()
    # Optional task scoping via ?task_id= at connect time.
    active_websockets[websocket] = websocket.query_params.get("task_id")
    try:
        while True:
            raw = await websocket.receive_text()
            # Allow clients to (re)scope their subscription at runtime.
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(msg, dict):
                continue
            if msg.get("type") == "subscribe":
                active_websockets[websocket] = msg.get("task_id")
            elif msg.get("type") == "unsubscribe":
                active_websockets[websocket] = None
    except WebSocketDisconnect:
        active_websockets.pop(websocket, None)

# ── SQLite History Persistence Endpoints ────────────────────
# sqlite3 is a synchronous driver: run storage calls in worker threads so
# they never block the event loop.

@app.get("/api/history")
async def get_history_records(limit: int = 50):
    """Retrieve history records stored in SQLite."""
    return await asyncio.to_thread(history_storage.list_records, limit=limit)

@app.post("/api/history")
async def save_history_record(record: Dict[str, Any]):
    """Save or update a history record in SQLite."""
    success = await asyncio.to_thread(history_storage.save_record, record)
    return {"status": "ok" if success else "error"}

@app.delete("/api/history/{record_id}")
async def delete_history_record(record_id: str):
    """Delete a history record from SQLite."""
    success = await asyncio.to_thread(history_storage.delete_record, record_id)
    return {"status": "ok" if success else "error"}

@app.delete("/api/history")
async def clear_all_history():
    """Clear all history records from SQLite."""
    success = await asyncio.to_thread(history_storage.clear_all)
    return {"status": "ok" if success else "error"}

# ── AI Accuracy Backtesting & Self-Optimization Endpoints ──

@app.get("/api/backtest/accuracy")
async def get_backtest_accuracy(force: bool = False):
    """Runs real price-based backtest evaluation and returns prediction accuracy & analyst rankings."""
    # Heavy sync work (yfinance + sqlite) — offload to a worker thread.
    return await asyncio.to_thread(accuracy_backtester.run_backtest, force=force)

@app.get("/api/experience")
async def get_experience_memory():
    """Regenerates data-grounded experience rules from the latest real backtest, then returns them."""
    stats = await asyncio.to_thread(accuracy_backtester.run_backtest)
    return await asyncio.to_thread(experience_service.regenerate_from_backtest, stats)

# ── User Watchlist & Analytics Endpoints ────────────────────

@app.get("/api/watchlist")
async def get_watchlist():
    """Returns user watchlist with current price, change %, latest verdict, and analysis count."""
    return await asyncio.to_thread(watchlist_service.list_watchlist)

class WatchlistAddRequest(BaseModel):
    symbol: str

@app.post("/api/watchlist")
async def add_watchlist_symbol(req: WatchlistAddRequest):
    """Add stock symbol to user watchlist."""
    success = await asyncio.to_thread(watchlist_service.add_symbol, req.symbol)
    return {"status": "ok" if success else "error"}

@app.delete("/api/watchlist/{symbol}")
async def remove_watchlist_symbol(symbol: str):
    """Remove stock symbol from user watchlist."""
    success = await asyncio.to_thread(watchlist_service.remove_symbol, symbol)
    return {"status": "ok" if success else "error"}

@app.get("/api/user/analytics")
async def get_user_analytics():
    """Returns summary analytics for user analysis activity."""
    return await asyncio.to_thread(watchlist_service.get_analytics_summary)

@app.post("/api/watchlist/refresh")
async def refresh_watchlist_prices():
    """Force an immediate real-time price refresh for all watchlist symbols."""
    watchlist_service.force_refresh()
    return {"status": "ok", "message": "Price refresh initiated"}
