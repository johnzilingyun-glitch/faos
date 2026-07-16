import pytest
import yfinance as yf
from unittest.mock import patch, MagicMock

from faos.services.provider.yfinance_impl import YFinanceQuoteProvider, YFinanceNewsProvider
from faos.services.provider.models import ProviderRequest

@pytest.fixture
def mock_yf_ticker():
    with patch('yfinance.Ticker') as mock_ticker_cls:
        mock_instance = MagicMock()
        mock_instance.info = {
            "currentPrice": 420.69,
            "previousClose": 415.00
        }
        mock_instance.news = [
            {"title": "MSFT announces new AI model", "publisher": "TechCrunch"},
            {"title": "Earnings beat expectations", "publisher": "WSJ"}
        ]
        mock_ticker_cls.return_value = mock_instance
        yield mock_ticker_cls

@pytest.mark.asyncio
async def test_yfinance_quote_provider(mock_yf_ticker):
    provider = YFinanceQuoteProvider()
    
    assert provider.manifest.category == "market"
    
    request = ProviderRequest(task_id="test", entity="MSFT", domain="quote")
    response = await provider.fetch(request)
    
    assert response.status == "success"
    data = response.data
    assert data["symbol"] == "MSFT"
    assert data["price"] == 420.69
    assert data["source"] == "YFinanceQuoteProvider"
    mock_yf_ticker.assert_called_once_with("MSFT")

@pytest.mark.asyncio
async def test_yfinance_news_provider(mock_yf_ticker):
    provider = YFinanceNewsProvider()
    
    assert provider.manifest.category == "news"
    
    request = ProviderRequest(task_id="test", entity="MSFT", domain="news")
    response = await provider.fetch(request)
    
    assert response.status == "success"
    data = response.data
    assert len(data) == 2
    assert data[0]["title"] == "MSFT announces new AI model"
    assert data[0]["sentiment"] == 0.5
    assert data[0]["source"] == "YFinanceNewsProvider"
    
    assert data[1]["publisher"] == "WSJ"
