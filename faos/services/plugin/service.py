import logging
from typing import List, Optional

from faos.services.plugin.models import PluginCategory, PluginInfo, PluginStatus
from faos.services.plugin.base import BasePlugin
from faos.services.plugin.registry import PluginRegistry
from faos.services.plugin.lifecycle import PluginLifecycleManager

logger = logging.getLogger(__name__)


class PluginService:
    """
    Plugin Service — the unified extension management interface for FAOS.

    Wraps the PluginRegistry and PluginLifecycleManager to provide a
    simple, high-level API that the TaskRuntime and other services use.
    """

    def __init__(self):
        self.registry = PluginRegistry()
        self.lifecycle = PluginLifecycleManager(self.registry)
        logger.info("PluginService initialized")

    # ── Plugin management ────────────────────────────────────────────

    async def register_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register, validate, initialize, and activate a native plugin
        in a single call.  Returns True if the plugin is now ACTIVE.
        """
        return await self.lifecycle.install_and_activate(plugin)

    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """Take a plugin offline (but keep it loaded for re-activation)."""
        return await self.lifecycle.deactivate_plugin(plugin_id)

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Fully unload a plugin, releasing all resources."""
        return await self.lifecycle.unload_plugin(plugin_id)

    # ── Query ────────────────────────────────────────────────────────

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin info by ID."""
        return self.registry.get(plugin_id)

    def get_plugin_instance(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get the live plugin instance by ID."""
        return self.registry.get_instance(plugin_id)

    def get_plugins_by_category(self, category: PluginCategory) -> List[PluginInfo]:
        """List all plugins that extend a given FAOS layer."""
        return self.registry.get_by_category(category)

    def get_active_plugins(self) -> List[PluginInfo]:
        """List all currently active plugins."""
        return self.registry.get_active()

    def get_all_plugins(self) -> List[PluginInfo]:
        """List every registered plugin regardless of status."""
        return self.registry.get_all()
