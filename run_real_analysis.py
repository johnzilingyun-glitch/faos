import asyncio
import os
import sys

# Force REAL mode
os.environ["FAOS_ENV"] = "real"

from faos.core.runtime import TaskRuntime
from faos.core.models import Event

async def main():
    runtime = TaskRuntime()
    runtime.start()

    print("Submitting Task to Analyze AAPL...")
    task = await runtime.submit_task("Analyze AAPL")
    task_id = task.id
    
    # Wait for execution to finish
    await asyncio.sleep(5)
    
    context = runtime.contexts.get(task_id)
    if not context:
        print("Error: Context not found.")
        await runtime.stop()
        return

    print("========================================")
    print("Report Generated with REAL Data:")
    print("========================================")
    
    report = context.results.get("report")
    if report:
        print(report)
    else:
        print("No report generated.")
        
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
