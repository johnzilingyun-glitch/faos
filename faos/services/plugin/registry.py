import logging
from typing import Dict, List, Optional

from faos.services.plugin.models import PluginCategory, PluginInfo, PluginManifest, PluginStatus
from faos.services.plugin.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Central registry that tracks all discovered and loaded plugins.

    Responsibilities (from Chapter 16 spec):
      - Plugin ID → PluginInfo mapping
      - Lookup by category
      - Status transitions
      - Dependency resolution helpers
    """

    def __init__(self):
        self._plugins: Dict[str, PluginInfo] = {}
        self._instances: Dict[str, BasePlugin] = {}

    # ── Registration ─────────────────────────────────────────────────

    def register(self, manifest: PluginManifest, instance: Optional[BasePlugin] = None) -> PluginInfo:
        """Register a plugin manifest (and optional instance) in the registry."""
        if manifest.id in self._plugins:
            logger.warning(f"Plugin '{manifest.id}' is being re-registered; overwriting.")

        info = PluginInfo(manifest=manifest, status=PluginStatus.DISCOVERED)
        self._plugins[manifest.id] = info

        if instance is not None:
            self._instances[manifest.id] = instance

        logger.info(f"Plugin registered: {manifest.id} ({manifest.category})")
        return info

    def set_instance(self, plugin_id: str, instance: BasePlugin):
        """Attach a live plugin instance after loading."""
        self._instances[plugin_id] = instance

    # ── Lookup ───────────────────────────────────────────────────────

    def get(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin info by ID."""
        return self._plugins.get(plugin_id)

    def get_instance(self, plugin_id: str) -> Optional[BasePlugin]:
        """Get the live plugin instance by ID."""
        return self._instances.get(plugin_id)

    def get_by_category(self, category: PluginCategory) -> List[PluginInfo]:
        """Return all plugins that extend a given FAOS layer."""
        return [p for p in self._plugins.values() if p.manifest.category == category]

    def get_active(self) -> List[PluginInfo]:
        """Return all plugins currently in ACTIVE status."""
        return [p for p in self._plugins.values() if p.status == PluginStatus.ACTIVE]

    def get_all(self) -> List[PluginInfo]:
        """Return every registered plugin regardless of status."""
        return list(self._plugins.values())

    # ── Status transitions ───────────────────────────────────────────

    def update_status(self, plugin_id: str, status: PluginStatus, error: Optional[str] = None):
        """Transition a plugin to a new lifecycle status."""
        info = self._plugins.get(plugin_id)
        if info is None:
            logger.error(f"Cannot update status: plugin '{plugin_id}' not found.")
            return
        old = info.status
        info.status = status
        if error:
            info.error_message = error
        logger.debug(f"Plugin '{plugin_id}': {old} → {status}")

    # ── Dependency helpers ───────────────────────────────────────────

    def check_dependencies(self, plugin_id: str) -> List[str]:
        """
        Return a list of *missing* dependency IDs for a plugin.
        An empty list means all dependencies are satisfied.
        """
        info = self._plugins.get(plugin_id)
        if info is None:
            return [plugin_id]  # the plugin itself doesn't exist

        missing = []
        for dep_id in info.manifest.dependencies:
            dep = self._plugins.get(dep_id)
            if dep is None or dep.status in (PluginStatus.ERROR, PluginStatus.UNLOADED):
                missing.append(dep_id)
        return missing
