from abc import ABC, abstractmethod
from faos.services.plugin.models import PluginManifest


class BasePlugin(ABC):
    """
    Abstract base class for all native (in-process Python) plugins.

    Every plugin must:
      1. Expose a ``manifest`` property describing itself.
      2. Implement lifecycle hooks that the PluginLifecycleManager will call.

    Lifecycle hooks are called in this order:
      on_init()  →  on_activate()  →  on_deactivate()  →  on_unload()
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the declarative manifest for this plugin."""
        ...

    # ── Lifecycle hooks ──────────────────────────────────────────────

    async def on_init(self):
        """Called once after the plugin is loaded and validated.
        Use this to allocate resources, read config, etc."""
        pass

    async def on_activate(self):
        """Called when the plugin transitions to ACTIVE.
        The plugin is now ready to serve requests."""
        pass

    async def on_deactivate(self):
        """Called when the plugin is being taken offline but not yet unloaded."""
        pass

    async def on_unload(self):
        """Called when the plugin is being removed.
        Release all resources here."""
        pass
