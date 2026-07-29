import logging
from typing import Dict, Optional
from faos.services.capability.models import CapabilityManifest

logger = logging.getLogger(__name__)

class CapabilityService:
    """
    Capability Service is the capability catalog of FAOS.

    The single source of truth for routing is the Skill registry (SkillService):
    every SkillManifest declares a canonical ``cap.<name>`` capability id.
    This catalog mirrors those ids (see ``register_from_skill``) so the
    Planner / MCP layer can discover what the system can do.

    Lookups accept either the manifest name or the canonical capability id.
    """
    def __init__(self):
        self._by_name: Dict[str, CapabilityManifest] = {}
        self._by_id: Dict[str, CapabilityManifest] = {}
        logger.info("CapabilityService initialized")

    def register_capability(self, manifest: CapabilityManifest):
        self._by_name[manifest.name] = manifest
        self._by_id[manifest.id] = manifest
        logger.info(f"Capability registered: {manifest.name} ({manifest.id})")

    def register_from_skill(self, skill_manifest) -> CapabilityManifest:
        """Derive and register a CapabilityManifest from a SkillManifest."""
        manifest = CapabilityManifest(
            id=skill_manifest.capability,
            name=skill_manifest.name,
            description=getattr(skill_manifest, "description", "") or "",
        )
        self.register_capability(manifest)
        return manifest

    def get_capability(self, name_or_id: str) -> Optional[CapabilityManifest]:
        return self._by_name.get(name_or_id) or self._by_id.get(name_or_id)

    def list_capabilities(self) -> Dict[str, CapabilityManifest]:
        """Return all registered capabilities keyed by canonical id."""
        return dict(self._by_id)
