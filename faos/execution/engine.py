import asyncio
import logging
from typing import Dict, Any, Set
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.event_bus import EventBus
from faos.core.context import ExecutionContext
from faos.services.skill.service import SkillService
from faos.services.skill.models import SkillRequest

logger = logging.getLogger(__name__)

class ExecutionEngine:
    """
    DAG execution engine for FAOS.
    Subscribes to ExecutionPlanGenerated events and schedules/executes PlanNodes.
    """
    def __init__(self, event_bus: EventBus, contexts: Dict[str, ExecutionContext], skill_service: SkillService = None):
        self.event_bus = event_bus
        self.contexts = contexts
        self.skill_service = skill_service
        self.event_bus.subscribe("ExecutionPlanGenerated", self._handle_plan_generated)

    async def _handle_plan_generated(self, event: Event):
        task_id = event.payload.get("task_id")
        plan_data = event.payload.get("plan")
        if not task_id or not plan_data:
            logger.error("ExecutionPlanGenerated event missing task_id or plan")
            return

        try:
            plan = ExecutionPlan.model_validate(plan_data)
        except Exception as e:
            logger.error(f"Failed to validate ExecutionPlan for task {task_id}: {e}")
            return

        logger.info(f"ExecutionEngine starting plan for task {task_id}")
        asyncio.create_task(self.execute(plan))

    async def execute(self, plan: ExecutionPlan):
        task_id = plan.task_id
        context = self.contexts.get(task_id)
        if not context:
            error_msg = f"No ExecutionContext found for task {task_id}"
            logger.error(error_msg)
            await self._fail_task(task_id, error_msg)
            return

        # Publish ExecutionStarted event
        started_event = Event(
            type="ExecutionStarted",
            source="ExecutionEngine",
            payload={"task_id": task_id}
        )
        await self.event_bus.publish(started_event)

        # Build node map and dependency structures
        nodes: Dict[str, PlanNode] = {node.id: node for node in plan.nodes}
        completed_nodes: Set[str] = set()
        running_nodes: Dict[str, asyncio.Task] = {}
        failed_nodes: Set[str] = set()

        all_node_ids = set(nodes.keys())

        # Simple cycle check
        # (Topological sort verification to prevent infinite loop)
        try:
            self._verify_no_cycles(nodes)
        except ValueError as e:
            error_msg = f"Invalid plan: {e}"
            logger.error(error_msg)
            await self._fail_task(task_id, error_msg)
            return

        try:
            while len(completed_nodes) + len(failed_nodes) < len(all_node_ids):
                # Find nodes ready to execute
                ready_nodes = []
                for node_id, node in nodes.items():
                    if node_id in completed_nodes or node_id in failed_nodes or node_id in running_nodes:
                        continue
                    # Check if all dependencies are completed
                    if all(dep in completed_nodes for dep in node.dependencies):
                        ready_nodes.append(node)

                # Start ready nodes
                for node in ready_nodes:
                    task = asyncio.create_task(self._execute_node(task_id, node, context))
                    running_nodes[node.id] = task

                if not running_nodes:
                    # No nodes are running and we haven't finished all nodes
                    # This shouldn't happen if cycle check passed, but just in case:
                    unexecuted = all_node_ids - completed_nodes - failed_nodes
                    error_msg = f"Execution stalled. Unexecuted nodes: {unexecuted}"
                    logger.error(error_msg)
                    await self._fail_task(task_id, error_msg)
                    return

                # Wait for at least one task to complete
                done, _ = await asyncio.wait(
                    running_nodes.values(),
                    return_when=asyncio.FIRST_COMPLETED
                )

                # Process completed tasks
                for finished_task in done:
                    # Find which node completed
                    finished_node_id = None
                    for nid, t in running_nodes.items():
                        if t == finished_task:
                            finished_node_id = nid
                            break

                    if finished_node_id:
                        del running_nodes[finished_node_id]
                        try:
                            # Retrieve the task result or propagate exception
                            await finished_task
                            completed_nodes.add(finished_node_id)
                        except Exception as e:
                            logger.error(f"Node {finished_node_id} failed: {e}")
                            failed_nodes.add(finished_node_id)
                            # On failure, cancel all other running tasks
                            for nid, t in running_nodes.items():
                                t.cancel()
                            raise e

            # If we reach here, all nodes completed successfully
            completion_event = Event(
                type="TaskCompleted",
                source="ExecutionEngine",
                payload={"task_id": task_id, "result": "Task execution completed successfully."}
            )
            await self.event_bus.publish(completion_event)
            logger.info(f"Task {task_id} execution completed successfully")

        except Exception as e:
            error_msg = f"Task {task_id} failed during execution: {e}"
            logger.error(error_msg)
            await self._fail_task(task_id, str(e))

    async def _fail_task(self, task_id: str, error_msg: str):
        failed_event = Event(
            type="TaskFailed",
            source="ExecutionEngine",
            payload={"task_id": task_id, "error": error_msg}
        )
        await self.event_bus.publish(failed_event)

    async def _execute_node(self, task_id: str, node: PlanNode, context: ExecutionContext):
        logger.info(f"Starting execution of node {node.id} ({node.capability})")
        # Publish NodeStarted event
        started_event = Event(
            type="NodeStarted",
            source="ExecutionEngine",
            payload={"task_id": task_id, "node_id": node.id, "capability": node.capability}
        )
        await self.event_bus.publish(started_event)

        try:
            if not self.skill_service:
                raise RuntimeError("SkillService is not initialized")
                
            skill_request = SkillRequest(
                task_id=task_id,
                parameters=node.parameters or {},
                context=context
            )
            
            response = await self.skill_service.execute_capability(node.capability, skill_request)
            
            if response.status == "failed":
                raise RuntimeError(response.error or f"Skill for {node.capability} failed")
                
            output = {"status": "success", "result": response.output}

            # Publish NodeCompleted event with context results snapshot
            completed_event = Event(
                type="NodeCompleted",
                source="ExecutionEngine",
                payload={
                    "task_id": task_id,
                    "node_id": node.id,
                    "capability": node.capability,
                    "output": output,
                    "results": dict(context.results)
                }
            )
            await self.event_bus.publish(completed_event)
            logger.info(f"Completed execution of node {node.id} ({node.capability})")

        except Exception as e:
            node_failed_event = Event(
                type="NodeFailed",
                source="ExecutionEngine",
                payload={"task_id": task_id, "node_id": node.id, "error": str(e)}
            )
            await self.event_bus.publish(node_failed_event)
            raise e

    def _verify_no_cycles(self, nodes: Dict[str, PlanNode]):
        """Simple topological sort cycle detection."""
        visited = {}  # 0: unvisited, 1: visiting, 2: visited
        for node_id in nodes:
            visited[node_id] = 0

        def dfs(node_id):
            visited[node_id] = 1
            node = nodes[node_id]
            for dep in node.dependencies:
                if dep not in nodes:
                    # Dependency on a node not in the plan is invalid
                    raise ValueError(f"Node {node_id} depends on non-existent node {dep}")
                if visited[dep] == 1:
                    raise ValueError(f"Cycle detected involving node {node_id} and dependency {dep}")
                if visited[dep] == 0:
                    dfs(dep)
            visited[node_id] = 2

        for node_id in nodes:
            if visited[node_id] == 0:
                dfs(node_id)
