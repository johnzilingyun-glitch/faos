import logging
from typing import Optional

from faos.core.event_bus import EventBus
from faos.core.models import Event
from faos.services.observability.trace_center import TraceCenter
from faos.services.observability.metrics_center import MetricsCenter
from faos.services.observability.timeline import RuntimeTimeline

logger = logging.getLogger(__name__)


class ObservabilityService:
    """
    Observability Service — The Runtime Nervous System of FAOS (Chapter 17).
    Manages tracing, metrics, and runtime timeline.
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self.traces = TraceCenter()
        self.metrics = MetricsCenter()
        self.timeline = RuntimeTimeline()
        
        if event_bus:
            self._attach_to_bus(event_bus)
            
        logger.info("ObservabilityService initialized")
        
    def _attach_to_bus(self, event_bus: EventBus):
        """Subscribe to all events to build the Runtime Timeline."""
        # Using a wildcard subscription (handled in our EventBus as "*")
        event_bus.subscribe("*", self._handle_event)
        logger.info("ObservabilityService attached to EventBus")

    async def _handle_event(self, event: Event):
        """Process incoming events for the timeline."""
        try:
            self.timeline.record_event(event)
        except Exception as e:
            logger.error(f"Error recording timeline event: {e}")
