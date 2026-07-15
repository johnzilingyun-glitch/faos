from typing import Any, Dict, List
from pydantic import BaseModel, Field

class ExecutionContext(BaseModel):
    """
    Shared context for the entire Task lifecycle.
    """
    task_id: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    provider_outputs: Dict[str, Any] = Field(default_factory=dict)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    trace: List[Dict[str, Any]] = Field(default_factory=list)
    
    def set_variable(self, key: str, value: Any):
        self.variables[key] = value
        
    def get_variable(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)
        
    def add_result(self, step_name: str, result: Any):
        self.results[step_name] = result
        
    def add_provider_output(self, provider_name: str, data: Any):
        self.provider_outputs[provider_name] = data
        
    def add_decision(self, decision: Dict[str, Any]):
        self.decisions.append(decision)
        
    def add_trace(self, log_entry: Dict[str, Any]):
        self.trace.append(log_entry)
