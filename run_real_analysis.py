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
    print("Waiting 60 seconds for multi-stage agents to run...")
    await asyncio.sleep(60)
    
    context = runtime.contexts.get(task_id)
    if not context:
        print("Error: Context not found.")
        await runtime.stop()
        return

    print("========================================")
    print("Multi-Agent Discussion Results:")
    print("========================================")
    
    discussion = context.results.get("discussion")
    if discussion:
        for op in discussion.get("opinions", []):
            print(f"[{op['name']}] Confidence: {op['confidence']:.2f}")
            print(f"  {op['opinion'][:200]}...")
            print()
        print(f"[CONSENSUS]:\n{discussion.get('consensus')}")
        print()
    else:
        print("No discussion generated.\n")

    print("========================================")
    print("Final Decision:")
    print("========================================")
    decision = context.results.get("decision")
    if decision:
        print(f"Action: {decision['action']}")
        print(f"Score: {decision.get('score', 'N/A')}")
        print(f"Confidence: {decision['confidence']}")
        print(f"Risk: {decision.get('risk', 'N/A')}")
        print(f"Strategy: {decision['strategy']}")
        print(f"Reason: {decision['reason']}")
    else:
        print("No decision generated.")
        
    print("\n========================================")
    print("Reflection (Self-Review):")
    print("========================================")
    reflection = context.results.get("reflection")
    if reflection:
        print(f"Passed: {reflection['is_passed']}")
        print(f"Confidence: {reflection['confidence']}")
        print(f"Feedback: {reflection['feedback']}")
    else:
        print("No reflection generated.")
    
    print("\n========================================")
    print("Report Generated with REAL Data:")
    print("========================================")
    
    report = context.results.get("report")
    if report:
        print(report)
    else:
        print("No report generated.")
        
    print("\n========================================")
    print("Runtime Timeline:")
    print("========================================")
    print(runtime.observability.timeline.dump_timeline_string(task_id))
        
    await runtime.stop()

if __name__ == "__main__":
    asyncio.run(main())
