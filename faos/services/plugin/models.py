from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Execution mode of a plugin."""
    NATIVE = "native"       # In-process Python
    REST = "rest"           # HTTP API
    MCP = "mcp"             # Model Context Protocol
    DOCKER = "docker"       # Docker container
    REMOTE = "remote"       # RPC/gRPC
    AI = "ai"               # External AI service


class PluginCategory(str, Enum):
    """Which FAOS layer this plugin extends."""
    DOMAIN = "domain"
    CAPABILITY = "capability"
    WORKFLOW = "workflow"
    SKILL = "skill"
    PROVIDER = "provider"
    CONNECTOR = "connector"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    DECISION = "decision"
    REPORT = "report"


class PluginStatus(str, Enum):
    """Lifecycle status of a plugin instance."""
    DISCOVERED = "discovered"
    LOADED = "loaded"
    VALIDATED = "validated"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    ERROR = "error"
    UNLOADED = "unloaded"


class PluginManifest(BaseModel):
    """
    Declarative manifest that every plugin must provide.
    This is the plugin's unique identity card.
    """
    id: str = Field(..., description="Unique plugin identifier (e.g. 'provider.eastmoney')")
    name: str = Field(..., description="Human-readable name")
    version: str = Field(default="1.0.0", description="Semantic version")
    type: PluginType = Field(default=PluginType.NATIVE, description="Execution mode")
    category: PluginCategory = Field(..., description="Which FAOS layer this plugin extends")
    author: str = Field(default="FAOS", description="Plugin author")
    description: str = Field(default="", description="What this plugin does")
    dependencies: List[str] = Field(default_factory=list, description="IDs of plugins this depends on")
    permissions: List[str] = Field(default_factory=list, description="Required permissions (e.g. 'market.read')")
    entry: Optional[str] = Field(default=None, description="Entry point file or module path")
    compatible_runtime: str = Field(default=">=5.0", description="Compatible FAOS runtime version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional plugin metadata")


class PluginInfo(BaseModel):
    """
    Runtime state wrapper that tracks a plugin's manifest plus its
    current lifecycle status and optional error information.
    """
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.DISCOVERED
    error_message: Optional[str] = None

    # The actual plugin instance is stored separately (not serialised).
    class Config:
        arbitrary_types_allowed = True
