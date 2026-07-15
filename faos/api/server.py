import asyncio
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from faos.core.runtime import TaskRuntime
from faos.core.models import Event

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

# We simulate the MockPlanner here for the API as well so the system actually does something
async def mock_planner_service(event: Event, event_bus):
    logger.info(f"MockPlanner received Event: {event.type} from {event.source} with payload: {event.payload}")
    task_id = event.payload.get("task_id")
    
    # Simulate processing time
    await asyncio.sleep(2)
    logger.info(f"MockPlanner generated plan for Task {task_id}")
    
    completion_event = Event(
        type="TaskCompleted",
        source="MockPlanner",
        payload={"task_id": task_id, "result": "Task execution successful!"}
    )
    await event_bus.publish(completion_event)

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
    
    # Subscribe the mock planner to TaskSubmitted
    runtime.event_bus.subscribe("TaskSubmitted", lambda e: mock_planner_service(e, runtime.event_bus))
    
    logger.info("FAOS API Server started.")

@app.on_event("shutdown")
async def shutdown_event():
    await runtime.stop()

@app.post("/api/tasks")
async def submit_task(req: TaskRequest):
    task = await runtime.submit_task(req.intent, req.context)
    return {"task_id": task.id, "status": "submitted"}

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
