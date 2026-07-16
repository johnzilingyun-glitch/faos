from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class KnowledgeCategory(str, Enum):
    DOMAIN = "domain"
    INDUSTRY = "industry"
    FINANCIAL = "financial"
    MACRO = "macro"
    STRATEGY = "strategy"
    PROMPT = "prompt"
    REPORT = "report"
    CAPABILITY = "capability"

class KnowledgeItem(BaseModel):
    """
    A single unit of knowledge in the FAOS system.
    """
    id: str = Field(..., description="Unique identifier for the knowledge item (e.g. 'capability.financial_analysis')")
    name: str = Field(..., description="Human-readable name")
    category: KnowledgeCategory = Field(..., description="Category of the knowledge")
    domain: Optional[str] = Field(default=None, description="Applicable domain (e.g. 'stock', 'macro')")
    version: str = Field(default="1.0", description="Version of this knowledge item")
    description: str = Field(..., description="Detailed description of what this knowledge provides")
    content: Any = Field(default=None, description="The actual knowledge content (can be string, dict, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional properties or relations")

class KnowledgePackage(BaseModel):
    """
    A logical collection of KnowledgeItems, allowing bulk loading.
    """
    id: str = Field(..., description="Package identifier (e.g. 'valuation', 'macro-cn')")
    version: str = Field(default="1.0", description="Package version")
    domain: List[str] = Field(default_factory=list, description="Applicable domains")
    language: str = Field(default="zh-CN", description="Language of the knowledge package")
    includes: List[str] = Field(default_factory=list, description="List of KnowledgeItem IDs included in this package")
