import pytest
from faos.services.provider.service import ProviderService
from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider
from faos.services.provider.models import ProviderRequest

@pytest.mark.asyncio
async def test_provider_service_registration():
    service = ProviderService()
    quote_provider = MockQuoteProvider()
    
    service.register_provider(quote_provider)
    
    retrieved = service.get_provider("mock_quote")
    assert retrieved is not None
    assert retrieved.manifest.name == "Mock Quote Provider"

@pytest.mark.asyncio
async def test_provider_service_fetch():
    service = ProviderService()
    service.register_provider(MockQuoteProvider())
    service.register_provider(MockNewsProvider())
    
    req = ProviderRequest(entity="AAPL")
    
    # Test Quote Fetch
    quote_resp = await service.fetch_data("mock_quote", req)
    assert quote_resp.status == "success"
    assert quote_resp.data["symbol"] == "AAPL"
    assert quote_resp.data["price"] == 175.5
    
    # Test News Fetch
    news_resp = await service.fetch_data("mock_news", req)
    assert news_resp.status == "success"
    assert len(news_resp.data) == 2
    assert "AAPL" in news_resp.data[0]["title"]

@pytest.mark.asyncio
async def test_provider_service_not_found():
    service = ProviderService()
    req = ProviderRequest(entity="AAPL")
    
    resp = await service.fetch_data("invalid_provider", req)
    assert resp.status == "failed"
    assert "not found" in resp.error
