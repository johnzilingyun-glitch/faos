import asyncio
from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderRequest, ProviderResponse, ProviderManifest

class MockQuoteProvider(BaseProvider):
    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="mock_quote",
            name="Mock Quote Provider",
            category="market",
            capabilities=["realtime_quote"]
        )
        
    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        await asyncio.sleep(0.5)
        # Standard Data Model for Quote
        data = {
            "symbol": request.entity,
            "market": "US",
            "price": 175.5,
            "change": 1.2,
            "volume": 50000000,
            "source": "MockQuoteProvider"
        }
        return ProviderResponse(status="success", data=data)

class MockNewsProvider(BaseProvider):
    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="mock_news",
            name="Mock News Provider",
            category="news",
            capabilities=["news_search"]
        )
        
    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        await asyncio.sleep(0.5)
        # Standard Data Model for News
        data = [
            {"title": f"New product launch for {request.entity}", "sentiment": 0.8, "source": "MockNewsProvider"},
            {"title": f"{request.entity} stock reaches new high", "sentiment": 0.7, "source": "MockNewsProvider"}
        ]
        return ProviderResponse(status="success", data=data)
