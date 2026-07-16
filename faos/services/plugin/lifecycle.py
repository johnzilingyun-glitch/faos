import logging
from typing import Optional

from faos.services.plugin.models import PluginStatus
from faos.services.plugin.base import BasePlugin
from faos.services.plugin.registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLifecycleManager:
    """
    Drives a plugin through its lifecycle stages:

        Discover → Load → Validate → Initialize → Activate
                                                      ↓
                                               Deactivate → Unload

    Each transition calls the corresponding hook on the plugin instance
    and updates the registry status accordingly.
    """

    def __init__(self, registry: PluginRegistry):
        self._registry = registry

    # ── Public API ───────────────────────────────────────────────────

    async def load_plugin(self, plugin: BasePlugin) -> bool:
        """
        Register a native plugin, validate its manifest, and transition
        it to LOADED status.
        """
        manifest = plugin.manifest
        info = self._registry.register(manifest, instance=plugin)

        # Validate manifest
        if not self._validate_manifest(manifest.id):
            return False

        self._registry.update_status(manifest.id, PluginStatus.LOADED)
        return True

    async def initialize_plugin(self, plugin_id: str) -> bool:
        """
        Check dependencies and call on_init() on the plugin.
        Transitions to INITIALIZED on success, ERROR on failure.
        """
        instance = self._registry.get_instance(plugin_id)
        if instance is None:
            logger.error(f"Cannot initialize '{plugin_id}': no instance found.")
            self._registry.update_status(plugin_id, PluginStatus.ERROR, "No instance")
            return False

        # Check dependencies
        missing = self._registry.check_dependencies(plugin_id)
        if missing:
            msg = f"Missing dependencies: {missing}"
            logger.error(f"Plugin '{plugin_id}': {msg}")
            self._registry.update_status(plugin_id, PluginStatus.ERROR, msg)
            return False

        try:
            await instance.on_init()
            self._registry.update_status(plugin_id, PluginStatus.INITIALIZED)
            logger.info(f"Plugin '{plugin_id}' initialized successfully.")
            return True
        except Exception as e:
            msg = f"on_init() failed: {e}"
            logger.error(f"Plugin '{plugin_id}': {msg}")
            self._registry.update_status(plugin_id, PluginStatus.ERROR, msg)
            return False

    async def activate_plugin(self, plugin_id: str) -> bool:
        """
        Call on_activate() and transition to ACTIVE.
        The plugin is now serving requests.
        """
        instance = self._registry.get_instance(plugin_id)
        if instance is None:
            logger.error(f"Cannot activate '{plugin_id}': no instance found.")
            return False

        try:
            await instance.on_activate()
            self._registry.update_status(plugin_id, PluginStatus.ACTIVE)
            logger.info(f"Plugin '{plugin_id}' activated.")
            return True
        except Exception as e:
            msg = f"on_activate() failed: {e}"
            logger.error(f"Plugin '{plugin_id}': {msg}")
            self._registry.update_status(plugin_id, PluginStatus.ERROR, msg)
            return False

    async def deactivate_plugin(self, plugin_id: str) -> bool:
        """Call on_deactivate() and transition to LOADED (can be re-activated)."""
        instance = self._registry.get_instance(plugin_id)
        if instance is None:
            return False

        try:
            await instance.on_deactivate()
            self._registry.update_status(plugin_id, PluginStatus.LOADED)
            logger.info(f"Plugin '{plugin_id}' deactivated.")
            return True
        except Exception as e:
            logger.error(f"Plugin '{plugin_id}' deactivation error: {e}")
            return False

    async def unload_plugin(self, plugin_id: str) -> bool:
        """Call on_unload() and transition to UNLOADED."""
        instance = self._registry.get_instance(plugin_id)
        if instance is None:
            return False

        try:
            await instance.on_unload()
            self._registry.update_status(plugin_id, PluginStatus.UNLOADED)
            logger.info(f"Plugin '{plugin_id}' unloaded.")
            return True
        except Exception as e:
            logger.error(f"Plugin '{plugin_id}' unload error: {e}")
            return False

    # ── Full lifecycle shortcut ──────────────────────────────────────

    async def install_and_activate(self, plugin: BasePlugin) -> bool:
        """
        Convenience: Load → Initialize → Activate in one call.
        Returns True only if all stages succeed.
        """
        if not await self.load_plugin(plugin):
            return False
        plugin_id = plugin.manifest.id
        if not await self.initialize_plugin(plugin_id):
            return False
        if not await self.activate_plugin(plugin_id):
            return False
        return True

    # ── Internal helpers ─────────────────────────────────────────────

    def _validate_manifest(self, plugin_id: str) -> bool:
        """Basic manifest validation."""
        info = self._registry.get(plugin_id)
        if info is None:
            return False

        manifest = info.manifest
        if not manifest.id or not manifest.name:
            msg = "Manifest is missing required fields (id, name)."
            logger.error(f"Plugin '{plugin_id}': {msg}")
            self._registry.update_status(plugin_id, PluginStatus.ERROR, msg)
            return False

        self._registry.update_status(plugin_id, PluginStatus.VALIDATED)
        return True
