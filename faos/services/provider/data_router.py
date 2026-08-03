"""
DataRouter — Market-aware data source router with fallback.

Implements the Strategy Pattern: detects market from ticker and
routes to the optimal data provider. Falls back gracefully on failure.

Routing rules:
  A-Shares (6-digit)         → AStockDirectProvider (primary)
  HK (.HK / 4-5 digit)       → YFinanceProvider
  US (alpha / ^prefix)       → YFinanceProvider
"""

import logging
from typing import Dict, Any, Optional

from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderRequest, ProviderResponse
from faos.services.provider.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

class DataRouter:
    """
    Intelligent data router that selects the optimal provider based on market.
    Provides a unified interface hiding all underlying API complexity.
    """

    def __init__(self, provider_service):
        self.provider_service = provider_service
        self._circuit_breaker = CircuitBreaker(max_failures=3, cooldown_seconds=300)
        
        # We assume provider_service has registered these IDs
        self.a_stock_id = "a_stock_direct"
        self.yfinance_id = "yfinance_quote"
        self.mock_id = "mock_quote"

    def detect_market(self, symbol: str) -> str:
        """Heuristic to detect market from symbol."""
        s = symbol.strip().upper()
        if s.endswith(".HK") or s.startswith("HK") or (len(s) == 5 and s.isdigit()):
            return "HK-Share"
        # A-Share: 6-digit with optional .SS/.SZ/.SH/.BJ suffix
        if s.endswith((".SS", ".SZ", ".SH", ".BJ")):
            code = s.rsplit(".", 1)[0]
            if code.isdigit() and len(code) == 6:
                return "A-Share"
        if len(s) == 6 and s.isdigit():
            return "A-Share"
        if s.startswith("^") or s.isalpha():
            return "US-Share"
        return "Unknown"

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        """Route fetch request to the best provider with fallback."""
        symbol = request.entity
        market = self.detect_market(symbol)
        
        # Primary selection
        primary_id = self.a_stock_id if market == "A-Share" else self.yfinance_id
        fallback_id = self.yfinance_id if market == "A-Share" else self.a_stock_id
        
        providers_to_try = [primary_id, fallback_id, self.mock_id]
        
        for p_id in providers_to_try:
            # Skip if circuit breaker is open
            if self._circuit_breaker.is_open(p_id):
                logger.debug(f"[DataRouter] Skipping {p_id} (Circuit Breaker OPEN)")
                continue
                
            provider = self.provider_service.get_provider(p_id)
            if not provider:
                continue
                
            logger.info(f"[DataRouter] Attempting fetch with {p_id} for {symbol} ({market})")
            resp = await provider.fetch(request)
            
            if resp.status == "success":
                self._circuit_breaker.record_success(p_id)
                return resp
            else:
                logger.warning(f"[DataRouter] Provider {p_id} failed: {resp.error}")
                self._circuit_breaker.record_failure(p_id)
                
        return ProviderResponse(
            status="failed", 
            error=f"All providers failed for {symbol}"
        )
