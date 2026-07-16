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
    category: str = Field(..., description="Provider category (e.g., market, news, macro)")
    capabilities: List[str] = Field(default_factory=list, description="List of supported capabilities")
    supported_parameters: List[str] = Field(default_factory=list, description="Parameters supported by this provider")
    priority: int = Field(default=0, description="Routing priority. Higher value = higher priority")
    version: str = "1.0"
    description: str = ""
