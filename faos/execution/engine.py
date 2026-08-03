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

    Resilience policy:
    - Each node execution is bounded by ``node_timeout`` seconds.
    - A failing node is retried up to ``max_retries`` times with exponential
      backoff (a ``NodeRetrying`` event is published for observability).
    - If a node still fails after all retries, the task fails fast and any
      in-flight sibling nodes are cancelled.
    """
    def __init__(self, event_bus: EventBus, contexts: Dict[str, ExecutionContext],
                 skill_service: SkillService = None,
                 node_timeout: float = 300.0, max_retries: int = 1):
        self.event_bus = event_bus
        self.contexts = contexts
        self.skill_service = skill_service
        self.node_timeout = node_timeout
        self.max_retries = max(0, max_retries)
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

            response = await self._execute_with_retry(task_id, node, skill_request)

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
                    "results": context.snapshot_results()
                }
            )
            await self.event_bus.publish(completed_event)
            logger.info(f"Completed execution of node {node.id} ({node.capability})")

        except Exception as e:
            import traceback
            err_msg = str(e) if str(e) else f"{type(e).__name__} (no message)"
            logger.error(
                f"Node {node.id} ({node.capability}) FAILED: {type(e).__name__}: {err_msg}\n"
                f"{traceback.format_exc()}"
            )
            node_failed_event = Event(
                type="NodeFailed",
                source="ExecutionEngine",
                payload={"task_id": task_id, "node_id": node.id, "error": err_msg, "error_type": type(e).__name__}
            )
            await self.event_bus.publish(node_failed_event)
            raise e

    async def _execute_with_retry(self, task_id: str, node: PlanNode, skill_request: SkillRequest):
        """Run the skill bounded by a timeout, retrying transient failures.

        Note: SkillService converts skill exceptions into SkillResponse(status="failed"),
        so both raised exceptions and failed responses are treated as retryable here.
        """
        last_error: Exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await asyncio.wait_for(
                    self.skill_service.execute_capability(node.capability, skill_request),
                    timeout=self.node_timeout,
                )
                if response.status == "failed":
                    raise RuntimeError(response.error or f"Skill for {node.capability} failed")
                return response
            except asyncio.CancelledError:
                raise
            except Exception as e:
                last_error = e
                err_msg = str(e) if str(e) else f"{type(e).__name__} (no message)"
                if attempt >= self.max_retries:
                    break
                delay = min(2 ** attempt, 10)
                logger.warning(
                    f"Node {node.id} ({node.capability}) attempt {attempt + 1} failed: "
                    f"{type(e).__name__}: {err_msg}. Retrying in {delay}s..."
                )
                await self.event_bus.publish(Event(
                    type="NodeRetrying",
                    source="ExecutionEngine",
                    payload={
                        "task_id": task_id,
                        "node_id": node.id,
                        "capability": node.capability,
                        "attempt": attempt + 1,
                        "max_retries": self.max_retries,
                        "error": str(e),
                    },
                ))
                await asyncio.sleep(delay)
        logger.error(
            f"Node {node.id} ({node.capability}) FAILED after {self.max_retries + 1} attempts: "
            f"{type(last_error).__name__}: {str(last_error) if str(last_error) else '(no message)'}"
        )
        raise last_error

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
