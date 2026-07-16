import logging
from typing import Dict, Optional
from faos.services.capability.models import CapabilityManifest

logger = logging.getLogger(__name__)

class CapabilityService:
    """
    Capability Service is the capability center of FAOS.
    It manages the registry of CapabilityManifests, allowing Planner to discover capabilities.
    """
    def __init__(self):
        self._capabilities: Dict[str, CapabilityManifest] = {}
        logger.info("CapabilityService initialized")
        
    def register_capability(self, manifest: CapabilityManifest):
        self._capabilities[manifest.name] = manifest
        logger.info(f"Capability registered: {manifest.name} ({manifest.id})")
        
    def get_capability(self, name: str) -> Optional[CapabilityManifest]:
        return self._capabilities.get(name)
