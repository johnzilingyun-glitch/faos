import logging
from typing import Dict, Optional
from faos.services.workflow.models import WorkflowDefinition

logger = logging.getLogger(__name__)

class WorkflowService:
    """
    Workflow Service acts as the business orchestration center.
    It manages the registry of workflow templates that Planner can discover.
    """
    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        logger.info("WorkflowService initialized")

    def register_workflow(self, workflow: WorkflowDefinition):
        self.workflows[workflow.id] = workflow
        logger.info(f"Registered workflow: {workflow.id} ({workflow.name})")

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self.workflows.get(workflow_id)
