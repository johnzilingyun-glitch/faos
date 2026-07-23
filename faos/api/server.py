import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global runtime instance
runtime = TaskRuntime()
active_websockets = []

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

async def broadcast_event(event: Event):
    """Broadcasts an event to all connected WebSockets."""
    event_dict = event.model_dump()
    # Convert datetime to string for JSON serialization
    event_dict['timestamp'] = event_dict['timestamp'].isoformat()
    message = json.dumps(event_dict)
    
    for ws in list(active_websockets):
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to websocket: {e}")
            active_websockets.remove(ws)

@app.on_event("startup")
async def startup_event():
    runtime.start()
    
    # Subscribe the WebSocket broadcaster to all events
    runtime.event_bus.subscribe("*", broadcast_event)
    
    # Start background price refresh (every 10 minutes)
    watchlist_service.start_background_refresh()
    
    logger.info("FAOS API Server started.")

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

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            # We don't expect messages from client in this simple setup, 
            # but we need to keep the connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

# ── SQLite History Persistence Endpoints ────────────────────

@app.get("/api/history")
async def get_history_records(limit: int = 50):
    """Retrieve history records stored in SQLite."""
    return history_storage.list_records(limit=limit)

@app.post("/api/history")
async def save_history_record(record: Dict[str, Any]):
    """Save or update a history record in SQLite."""
    success = history_storage.save_record(record)
    return {"status": "ok" if success else "error"}

@app.delete("/api/history/{record_id}")
async def delete_history_record(record_id: str):
    """Delete a history record from SQLite."""
    success = history_storage.delete_record(record_id)
    return {"status": "ok" if success else "error"}

@app.delete("/api/history")
async def clear_all_history():
    """Clear all history records from SQLite."""
    success = history_storage.clear_all()
    return {"status": "ok" if success else "error"}

# ── AI Accuracy Backtesting & Self-Optimization Endpoints ──

@app.get("/api/backtest/accuracy")
async def get_backtest_accuracy(force: bool = False):
    """Runs real price-based backtest evaluation and returns prediction accuracy & analyst rankings."""
    return accuracy_backtester.run_backtest(force=force)

@app.get("/api/experience")
async def get_experience_memory():
    """Regenerates data-grounded experience rules from the latest real backtest, then returns them."""
    stats = accuracy_backtester.run_backtest()
    return experience_service.regenerate_from_backtest(stats)

# ── User Watchlist & Analytics Endpoints ────────────────────

@app.get("/api/watchlist")
async def get_watchlist():
    """Returns user watchlist with current price, change %, latest verdict, and analysis count."""
    return watchlist_service.list_watchlist()

class WatchlistAddRequest(BaseModel):
    symbol: str

@app.post("/api/watchlist")
async def add_watchlist_symbol(req: WatchlistAddRequest):
    """Add stock symbol to user watchlist."""
    success = watchlist_service.add_symbol(req.symbol)
    return {"status": "ok" if success else "error"}

@app.delete("/api/watchlist/{symbol}")
async def remove_watchlist_symbol(symbol: str):
    """Remove stock symbol from user watchlist."""
    success = watchlist_service.remove_symbol(symbol)
    return {"status": "ok" if success else "error"}

@app.get("/api/user/analytics")
async def get_user_analytics():
    """Returns summary analytics for user analysis activity."""
    return watchlist_service.get_analytics_summary()

@app.post("/api/watchlist/refresh")
async def refresh_watchlist_prices():
    """Force an immediate real-time price refresh for all watchlist symbols."""
    watchlist_service.force_refresh()
    return {"status": "ok", "message": "Price refresh initiated"}



