import asyncio
import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from faos.core.runtime import TaskRuntime

logger = logging.getLogger(__name__)

# Create the MCP server instance
mcp = FastMCP("FAOS-Agent-Server")

# Initialize TaskRuntime (this should ideally be singleton or injected, but we'll instantiate for the server)
# In a real environment, you'd configure the LLM provider before starting this.
runtime = TaskRuntime()

@mcp.tool()
async def submit_faos_task(intent: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Submit a task to the FAOS Agentic OS.
    
    Args:
        intent: The user's natural language intent or task description.
        context: Optional dictionary containing configuration or context variables 
                 (e.g., llm_config, user preferences).
    
    Returns:
        A string indicating the task ID and initial submission status.
    """
    if not runtime._running:
        runtime.start()
        
    logger.info(f"MCP received task submission: {intent}")
    task = await runtime.submit_task(intent, initial_context=context)
    
    # In a full MCP implementation, we might wait for the task to complete
    # and return the final report. For now, we return the Task ID.
    return f"Task submitted successfully. Task ID: {task.id}"

@mcp.tool()
async def get_faos_task_status(task_id: str) -> str:
    """
    Retrieve the status of a previously submitted FAOS task.
    
    Args:
        task_id: The ID of the task to check.
        
    Returns:
        A string describing the current status of the task.
    """
    if task_id not in runtime.active_tasks:
        return f"Task ID {task_id} not found in active tasks."
        
    task = runtime.active_tasks[task_id]
    return f"Task ID: {task.id}, Status: {task.status}"

# Resources could be used to expose FAOS internal context or knowledge base
@mcp.resource("faos://knowledge/base")
def get_knowledge_base() -> str:
    """Returns the registered capabilities and workflows in FAOS."""
    workflows = runtime.workflow_service.workflows.keys()
    capabilities = runtime.capability_service.capabilities.keys()
    
    return f"Workflows: {', '.join(workflows)}\nCapabilities: {', '.join(capabilities)}"
