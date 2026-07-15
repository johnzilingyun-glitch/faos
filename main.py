import asyncio
import logging
from faos.core.runtime import TaskRuntime
from faos.core.models import Event

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("faos.main")

async def mock_planner_service(event: Event, event_bus):
    """A mock Planner Pipeline service that reacts to TaskSubmitted"""
    logger.info(f"MockPlanner received Event: {event.type} from {event.source} with payload: {event.payload}")
    task_id = event.payload.get("task_id")
    
    # Simulate planning time
    await asyncio.sleep(1)
    logger.info(f"MockPlanner generated plan for Task {task_id}")
    
    completion_event = Event(
        type="TaskCompleted",
        source="MockPlanner",
        payload={"task_id": task_id, "result": "Mock plan execution successful"}
    )
    await event_bus.publish(completion_event)

async def main():
    logger.info("Initializing FAOS Task Runtime...")
    runtime = TaskRuntime()
    runtime.start()
    
    # Register our mock service
    runtime.event_bus.subscribe("TaskSubmitted", lambda e: mock_planner_service(e, runtime.event_bus))
    
    logger.info("Submitting a new Task: 'Analyze AAPL stock'")
    task = await runtime.submit_task("Analyze AAPL stock", initial_context={"symbol": "AAPL"})
    
    logger.info(f"Task ID created: {task.id}")
    
    # Wait for the async events to be processed
    await asyncio.sleep(2)
    
    logger.info(f"Final Task Status: {runtime.active_tasks[task.id].status}")
    
    logger.info("Stopping FAOS Task Runtime...")
    await runtime.stop()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
