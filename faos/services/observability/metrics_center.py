import logging
from typing import Dict, List, Optional
from datetime import datetime

from faos.services.observability.models import Metric, MetricType

logger = logging.getLogger(__name__)


class MetricsCenter:
    """
    Records and queries runtime metrics (counters, gauges, etc.).
    """

    def __init__(self):
        self._metrics: List[Metric] = []
        
    def record_metric(self, name: str, value: float, metric_type: str = MetricType.COUNTER, labels: Optional[Dict[str, str]] = None):
        """Record a single metric data point."""
        metric = Metric(
            name=name,
            value=value,
            type=metric_type,
            labels=labels or {}
        )
        self._metrics.append(metric)
        logger.debug(f"Recorded metric: {name}={value} ({metric_type})")
        
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Helper to record a counter."""
        self.record_metric(name, value, MetricType.COUNTER, labels)
        
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Helper to record a gauge (e.g., current active tasks)."""
        self.record_metric(name, value, MetricType.GAUGE, labels)

    def get_metrics_by_name(self, name: str) -> List[Metric]:
        """Retrieve all recorded metrics for a specific name."""
        return [m for m in self._metrics if m.name == name]

    def aggregate_counter(self, name: str) -> float:
        """Sum all values for a counter metric."""
        return sum(m.value for m in self._metrics if m.name == name and m.type == MetricType.COUNTER)
