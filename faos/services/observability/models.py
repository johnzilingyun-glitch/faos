from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class SpanStatus(str):
    OK = "ok"
    ERROR = "error"
    RUNNING = "running"


class Span(BaseModel):
    """Represents a unit of work (e.g., a specific skill execution)."""
    span_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: str = SpanStatus.RUNNING
    error: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def duration_ms(self) -> float:
        if not self.end_time:
            return (datetime.utcnow() - self.start_time).total_seconds() * 1000
        return (self.end_time - self.start_time).total_seconds() * 1000


class Trace(BaseModel):
    """Represents an entire Task lifecycle."""
    trace_id: str
    task_id: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    spans: List[Span] = Field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        if not self.end_time:
            return (datetime.utcnow() - self.start_time).total_seconds() * 1000
        return (self.end_time - self.start_time).total_seconds() * 1000


class MetricType(str):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


class Metric(BaseModel):
    """Represents a recorded measurement (e.g., Token usage, latency, cost)."""
    name: str
    value: float
    type: str = MetricType.COUNTER
    labels: Dict[str, str] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TimelineEvent(BaseModel):
    """A formatted entry for the Runtime Timeline feature."""
    timestamp: datetime
    message: str
    source: str
    task_id: str
