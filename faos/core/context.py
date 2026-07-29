import threading
from typing import Any, Dict, List
from pydantic import BaseModel, Field, PrivateAttr

class ExecutionContext(BaseModel):
    """
    Shared context for the entire Task lifecycle.

    DAG nodes may run in parallel (e.g. FetchData + FetchNews), so every
    mutation method is guarded by an internal lock to avoid lost updates.
    Read paths that only return a reference remain lock-free by design —
    use the snapshot_* helpers when a consistent copy is needed.
    """
    task_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    provider_outputs: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    fact_sheet: Dict[str, Any] = Field(default_factory=dict)
    evidence_graph: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=lambda: {
            "facts": [], "evidence": [], "signals": [],
            "inferences": [], "claims": [], "decisions": [],
        }
    )

    _lock: threading.Lock = PrivateAttr(default_factory=threading.Lock)

    def set_variable(self, key: str, value: Any):
        with self._lock:
            self.variables[key] = value

    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def add_result(self, step_name: str, result: Any):
        with self._lock:
            self.results[step_name] = result

    def add_provider_output(self, provider_name: str, data: Any):
        with self._lock:
            self.provider_outputs[provider_name] = data

    def add_decision(self, decision: Dict[str, Any]):
        with self._lock:
            self.decisions.append(decision)

    def add_trace(self, log_entry: Dict[str, Any]):
        with self._lock:
            self.trace.append(log_entry)

    def set_fact_sheet(self, fact_sheet: Dict[str, Any]):
        """Store the canonical FactSheet (built once) for the whole task."""
        with self._lock:
            self.fact_sheet = fact_sheet

    def add_evidence_node(self, kind: str, node: Dict[str, Any]):
        """Append a node to the shared evidence graph under the given kind
        (facts / evidence / signals / inferences / claims / decisions)."""
        with self._lock:
            self.evidence_graph.setdefault(kind, []).append(node)

    # ── Consistent snapshots for concurrent readers ────────────────

    def snapshot_results(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.results)

    def snapshot_provider_outputs(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.provider_outputs)
