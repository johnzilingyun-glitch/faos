import asyncio
import logging
from faos.core.runtime import TaskRuntime
from faos.core.models import Event

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("faos.main")

async def main():
    logger.info("Initializing FAOS Task Runtime...")
    runtime = TaskRuntime()
    runtime.start()
    
    logger.info("Submitting a new Task: 'Analyze AAPL stock'")
    task = await runtime.submit_task("Analyze AAPL stock", initial_context={"symbol": "AAPL"})
    
    logger.info(f"Task ID created: {task.id}")
    
    # Wait for the async events to be processed (Planner + DAG execution takes ~2.5s)
    await asyncio.sleep(4)
    
    # Inspect execution context
    context = runtime.get_context(task.id)
    if context:
        logger.info(f"Task variables: {context.variables}")
        logger.info(f"Task provider outputs: {list(context.provider_outputs.keys())}")
        logger.info(f"Task results: {list(context.results.keys())}")
        if "report" in context.results:
            logger.info("Generated Report Preview:\n" + context.results["report"])
    
    logger.info(f"Final Task Status: {runtime.active_tasks[task.id].status}")
    
    logger.info("Stopping FAOS Task Runtime...")
    await runtime.stop()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
