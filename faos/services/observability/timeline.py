import logging
from typing import Dict, List
from datetime import datetime

from faos.core.models import Event
from faos.services.observability.models import TimelineEvent

logger = logging.getLogger(__name__)


class RuntimeTimeline:
    """
    Subscribes to key events and constructs a chronological
    timeline of the Task lifecycle for debugging and UI display.
    """

    def __init__(self):
        self._timelines: Dict[str, List[TimelineEvent]] = {}
        
    def record_event(self, event: Event):
        """Translate a core Event into a human-readable TimelineEvent."""
        task_id = event.payload.get("task_id")
        if not task_id:
            # If no task_id, we can't associate it with a specific task timeline
            return
            
        message = self._format_event_message(event)
        
        timeline_event = TimelineEvent(
            timestamp=event.timestamp,
            message=message,
            source=event.source,
            task_id=task_id
        )
        
        if task_id not in self._timelines:
            self._timelines[task_id] = []
            
        self._timelines[task_id].append(timeline_event)
        logger.debug(f"Timeline [{task_id}]: {message}")

    def _format_event_message(self, event: Event) -> str:
        """Create a human-readable message based on event type."""
        e_type = event.type
        
        if e_type == "TaskCreated":
            return f"Task Created: {event.payload.get('intent', 'Unknown')}"
        elif e_type == "WorkflowSelected":
            return f"Workflow Selected: {event.payload.get('workflow_id')}"
        elif e_type == "SkillStarted":
            return f"Skill Started: {event.payload.get('skill_name', event.source)}"
        elif e_type == "SkillCompleted":
            return f"Skill Completed: {event.payload.get('skill_name', event.source)}"
        elif e_type == "ProviderInvoked":
            return f"Provider Invoked: {event.payload.get('provider_id')}"
        elif e_type == "DataReturned":
            return f"Data Returned from {event.source}"
        elif e_type == "ReasoningStarted":
            return "Reasoning Started"
        elif e_type == "ReasoningCompleted":
            return "Reasoning Completed"
        elif e_type == "DiscussionStarted":
            return "Expert Discussion Started"
        elif e_type == "DiscussionCompleted":
            return "Expert Discussion Finished"
        elif e_type == "DecisionGenerated":
            return "Decision Generated"
        elif e_type == "ReportExported":
            return "Report Exported"
        elif e_type == "Error":
            return f"Error: {event.payload.get('error_message', 'Unknown error')}"
        
        # Fallback for generic events
        return f"Event: {e_type} from {event.source}"

    def get_timeline(self, task_id: str) -> List[TimelineEvent]:
        """Get the chronological timeline for a specific task."""
        return self._timelines.get(task_id, [])
        
    def dump_timeline_string(self, task_id: str) -> str:
        """Format the timeline as a readable string."""
        events = self.get_timeline(task_id)
        if not events:
            return f"No timeline found for task {task_id}"
            
        lines = [f"=== Runtime Timeline for Task {task_id} ==="]
        for e in sorted(events, key=lambda x: x.timestamp):
            time_str = e.timestamp.strftime("%H:%M:%S")
            lines.append(f"{time_str}  {e.message}")
            
        return "\n".join(lines)
