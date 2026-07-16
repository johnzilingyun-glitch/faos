import pytest
from unittest.mock import AsyncMock, MagicMock

from faos.services.provider.models import ProviderManifest, ProviderRequest, ProviderResponse
from faos.services.provider.service import ProviderService
from faos.services.data_route.service import DataRouteService

@pytest.fixture
def mock_providers():
    high_priority_provider = MagicMock()
    high_priority_provider.manifest = ProviderManifest(
        id="high_priority",
        name="High Priority Provider",
        category="market",
        priority=100
    )
    
    low_priority_provider = MagicMock()
    low_priority_provider.manifest = ProviderManifest(
        id="low_priority",
        name="Low Priority Provider",
        category="market",
        priority=10
    )
    return high_priority_provider, low_priority_provider

@pytest.mark.asyncio
async def test_data_route_priority_routing(mock_providers):
    high_priority, low_priority = mock_providers
    
    provider_service = ProviderService()
    provider_service.register_provider(low_priority)
    provider_service.register_provider(high_priority)
    
    data_route = DataRouteService(provider_service)
    
    # Mock ProviderService.fetch_data to return success for high priority
    provider_service.fetch_data = AsyncMock(return_value=ProviderResponse(status="success", data={"price": 100}))
    
    request = ProviderRequest(entity="AAPL")
    response = await data_route.fetch_data("market", request)
    
    assert response.status == "success"
    assert response.data["price"] == 100
    
    # Assert that fetch_data was called ONLY once, and with the high_priority id
    provider_service.fetch_data.assert_called_once_with("high_priority", request)

@pytest.mark.asyncio
async def test_data_route_fallback(mock_providers):
    high_priority, low_priority = mock_providers
    
    provider_service = ProviderService()
    provider_service.register_provider(low_priority)
    provider_service.register_provider(high_priority)
    
    data_route = DataRouteService(provider_service)
    
    # Mock ProviderService.fetch_data to FAIL for high priority, but SUCCESS for low priority
    async def mock_fetch_data(provider_id, req):
        if provider_id == "high_priority":
            return ProviderResponse(status="failed", error="Network Timeout")
        return ProviderResponse(status="success", data={"price": 50})
        
    provider_service.fetch_data = AsyncMock(side_effect=mock_fetch_data)
    
    request = ProviderRequest(entity="AAPL")
    response = await data_route.fetch_data("market", request)
    
    assert response.status == "success"
    assert response.data["price"] == 50
    
    # Assert that fetch_data was called twice (once for high, once for low)
    assert provider_service.fetch_data.call_count == 2
    
@pytest.mark.asyncio
async def test_data_route_all_fail(mock_providers):
    high_priority, low_priority = mock_providers
    
    provider_service = ProviderService()
    provider_service.register_provider(low_priority)
    provider_service.register_provider(high_priority)
    
    data_route = DataRouteService(provider_service)
    
    provider_service.fetch_data = AsyncMock(return_value=ProviderResponse(status="failed", error="Error"))
    
    request = ProviderRequest(entity="AAPL")
    response = await data_route.fetch_data("market", request)
    
    assert response.status == "failed"
    assert "All providers for category 'market' failed" in response.error
