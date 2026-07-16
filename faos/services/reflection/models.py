from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ReflectionRequest(BaseModel):
    task_id: str
    target_data: Dict[str, Any] = Field(description="The data to be reviewed (e.g., decision result or discussion consensus)")
    llm_config: Optional[Dict[str, Any]] = None
    
class ReflectionResult(BaseModel):
    is_passed: bool = Field(description="Whether the reflection passed the consistency and fact check")
    confidence: float = Field(default=0.0)
    feedback: str = Field(description="Detailed feedback, hallucination warnings, or consistency flaws")
    revised_data: Optional[Dict[str, Any]] = Field(default=None, description="The corrected data if applicable")
