import logging
from typing import List

from faos.services.provider.service import ProviderService
from faos.services.provider.models import ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)

class DataRouteService:
    """
    Data Route Service sits between Skills and Provider Service.
    It is responsible for intelligent provider routing, prioritizing, and fallbacks.
    """
    def __init__(self, provider_service: ProviderService):
        self.provider_service = provider_service
        logger.info("DataRouteService initialized")

    async def fetch_data(self, category: str, request: ProviderRequest) -> ProviderResponse:
        """
        Fetch data for a given category with priority routing and automatic fallback.
        """
        logger.info(f"DataRoute requested for category: {category}, entity: {request.entity}")
        
        # 1. Find all providers matching the category
        matched_providers = []
        for p in self.provider_service.providers.values():
            if p.manifest.category == category:
                matched_providers.append(p)
                
        if not matched_providers:
            error_msg = f"No provider found for category: {category}"
            logger.error(error_msg)
            return ProviderResponse(status="failed", error=error_msg)
            
        # 2. Sort providers by priority descending
        matched_providers.sort(key=lambda x: x.manifest.priority, reverse=True)
        
        # 3. Try fetching data, fallback on failure
        last_error = None
        for provider in matched_providers:
            provider_id = provider.manifest.id
            logger.info(f"Routing request to provider: {provider_id} (Priority: {provider.manifest.priority})")
            
            try:
                # Assuming ProviderService.fetch_data is resilient, but we still handle failures here
                response = await self.provider_service.fetch_data(provider_id, request)
                if response.status == "success":
                    logger.info(f"Successfully fetched data from provider: {provider_id}")
                    return response
                else:
                    logger.warning(f"Provider {provider_id} returned failure: {response.error}. Attempting fallback...")
                    last_error = response.error
            except Exception as e:
                logger.warning(f"Provider {provider_id} threw exception: {e}. Attempting fallback...")
                last_error = str(e)
                
        # 4. If all providers failed
        error_msg = f"All providers for category '{category}' failed. Last error: {last_error}"
        logger.error(error_msg)
        return ProviderResponse(status="failed", error=error_msg)
