import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from faos.services.observability.models import Trace, Span, SpanStatus

logger = logging.getLogger(__name__)


class TraceCenter:
    """
    Manages the lifecycle of Traces and Spans.
    All modules share a single trace_id per Task.
    """

    def __init__(self):
        self._traces: Dict[str, Trace] = {}
        self._spans: Dict[str, Span] = {}

    def get_or_create_trace(self, task_id: str, trace_id: Optional[str] = None) -> Trace:
        """Get an existing trace for a task or create a new one."""
        # Find trace by task_id first
        for trace in self._traces.values():
            if trace.task_id == task_id:
                return trace
                
        if not trace_id:
            trace_id = str(uuid.uuid4())
            
        if trace_id not in self._traces:
            self._traces[trace_id] = Trace(trace_id=trace_id, task_id=task_id)
            logger.debug(f"Created trace {trace_id} for task {task_id}")
            
        return self._traces[trace_id]

    def start_span(self, trace_id: str, name: str, parent_span_id: Optional[str] = None, attributes: Optional[Dict] = None) -> Span:
        """Start a new span in a trace."""
        span = Span(
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            name=name,
            attributes=attributes or {}
        )
        self._spans[span.span_id] = span
        
        trace = self._traces.get(trace_id)
        if trace:
            trace.spans.append(span)
            
        logger.debug(f"Started span {span.span_id} ({name}) for trace {trace_id}")
        return span

    def end_span(self, span_id: str, status: str = SpanStatus.OK, error: Optional[str] = None):
        """End a span."""
        span = self._spans.get(span_id)
        if span:
            span.end_time = datetime.utcnow()
            span.status = status
            span.error = error
            logger.debug(f"Ended span {span_id} ({span.name}) with status {status}")
        else:
            logger.warning(f"Attempted to end unknown span {span_id}")

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a full trace."""
        return self._traces.get(trace_id)
