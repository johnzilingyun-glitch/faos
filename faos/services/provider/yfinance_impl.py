import logging
import yfinance as yf
from typing import Dict, Any, List

from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderManifest, ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)

class YFinanceQuoteProvider(BaseProvider):
    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="yfinance_quote",
            name="YFinance Quote Provider",
            category="market",
            capabilities=["realtime_quote"],
            priority=100
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        symbol = request.entity
        if not symbol:
            return ProviderResponse(status="failed", error="Entity (symbol) is required")

        logger.info(f"YFinanceQuoteProvider fetching quote for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try to get the most relevant price field
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0
            
            data = {
                "symbol": symbol,
                "price": price,
                "source": "YFinanceQuoteProvider"
            }
            return ProviderResponse(status="success", data=data)
        except Exception as e:
            logger.error(f"Error fetching quote for {symbol}: {e}")
            return ProviderResponse(status="failed", error=str(e))

class YFinanceNewsProvider(BaseProvider):
    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="yfinance_news",
            name="YFinance News Provider",
            category="news",
            capabilities=["news_search"],
            priority=100
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        symbol = request.entity
        if not symbol:
            return ProviderResponse(status="failed", error="Entity (symbol) is required")

        logger.info(f"YFinanceNewsProvider fetching news for {symbol}")
        
        try:
            ticker = yf.Ticker(symbol)
            raw_news = ticker.news
            
            results = []
            for item in raw_news[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "publisher": item.get("publisher", ""),
                    "sentiment": 0.5,  # Mock neutral sentiment
                    "source": "YFinanceNewsProvider"
                })
                
            return ProviderResponse(status="success", data=results)
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return ProviderResponse(status="failed", error=str(e))
