from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class ProviderRequest(BaseModel):
    entity: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class ProviderResponse(BaseModel):
    status: str = Field(..., description="Status of the provider fetch, e.g., 'success', 'failed'")
    data: Any = Field(None, description="Standard data model returned by provider")
    error: Optional[str] = Field(None, description="Error message if failed")

class ProviderManifest(BaseModel):
    id: str
    name: str
    category: str
    capabilities: List[str] = Field(default_factory=list)
    version: str = "1.0"
    description: str = ""
