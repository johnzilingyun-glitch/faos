import logging
from typing import Dict, Optional
from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)

class ProviderService:
    """
    Provider Service is the central registry and access point for all external data.
    """
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        logger.info("ProviderService initialized")

    def register_provider(self, provider: BaseProvider):
        manifest = provider.manifest
        self.providers[manifest.id] = provider
        logger.info(f"Registered provider: {manifest.id} ({manifest.name})")

    def get_provider(self, provider_id: str) -> Optional[BaseProvider]:
        return self.providers.get(provider_id)

    async def fetch_data(self, provider_id: str, request: ProviderRequest) -> ProviderResponse:
        provider = self.get_provider(provider_id)
        if not provider:
            error_msg = f"Provider not found: {provider_id}"
            logger.error(error_msg)
            return ProviderResponse(status="failed", error=error_msg)

        logger.info(f"Fetching data from provider: {provider_id} for entity: {request.entity}")
        try:
            return await provider.fetch(request)
        except Exception as e:
            logger.error(f"Provider {provider_id} fetch failed: {e}")
            return ProviderResponse(status="failed", error=str(e))
            
    async def fetch_by_category(self, category: str, request: ProviderRequest) -> ProviderResponse:
        # Simple routing: find first provider matching category
        matched = None
        for p in self.providers.values():
            if p.manifest.category == category:
                matched = p
                break
                
        if not matched:
            error_msg = f"No provider found for category: {category}"
            logger.error(error_msg)
            return ProviderResponse(status="failed", error=error_msg)
            
        return await self.fetch_data(matched.manifest.id, request)
