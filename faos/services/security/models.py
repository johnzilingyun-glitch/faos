from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class UserIdentity(BaseModel):
    user_id: str
    roles: List[str] = Field(default_factory=list)
    tenant_id: str = "default"

class GlobalPolicy(BaseModel):
    allow_network_access: bool = True
    allowed_providers: List[str] = Field(default_factory=lambda: ["*"])
    banned_providers: List[str] = Field(default_factory=list)
    max_tokens_per_task: int = 100000
    max_discussion_rounds: int = 5
    allow_export: bool = True

class SecretRef(BaseModel):
    key: str
    description: Optional[str] = None
