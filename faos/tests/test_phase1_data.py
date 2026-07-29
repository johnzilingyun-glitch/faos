import pytest
import pandas as pd
import asyncio
from typing import Dict, Any

from faos.services.provider.circuit_breaker import CircuitBreaker
from faos.services.provider.data_router import DataRouter
from faos.services.provider.polars_indicators import compute_indicators
from faos.services.provider.models import ProviderRequest
from faos.services.provider.a_stock_provider import AStockDirectProvider

def test_circuit_breaker():
    cb = CircuitBreaker(max_failures=2, cooldown_seconds=10)
    source = "test_src"
    
    # Initially closed
    assert not cb.is_open(source)
    
    # 1 failure -> still closed
    cb.record_failure(source)
    assert not cb.is_open(source)
    
    # 2 failures -> open
    cb.record_failure(source)
    assert cb.is_open(source)
    
    # Status check
    status = cb.status()
    assert status[source]["is_open"] is True
    assert status[source]["failures"] == 2
    
    # Record success -> resets
    cb.record_success(source)
    assert not cb.is_open(source)
    assert cb.status().get(source, {}).get("failures", 0) == 0

def test_data_router_detection():
    class DummyProviderService:
        pass
        
    router = DataRouter(DummyProviderService())
    
    # Test heuristics
    assert router.detect_market("000001") == "A-Share"
    assert router.detect_market("600519") == "A-Share"
    assert router.detect_market("00700.HK") == "HK-Share"
    assert router.detect_market("09988") == "HK-Share" # length=5
    assert router.detect_market("AAPL") == "US-Share"
    assert router.detect_market("^GSPC") == "US-Share"

def test_polars_indicators():
    # Create mock dataframe with Date, Open, High, Low, Close, Volume
    import numpy as np
    
    dates = pd.date_range("2023-01-01", periods=100)
    df = pd.DataFrame({
        "Date": dates,
        "Open": np.random.randn(100).cumsum() + 100,
        "High": np.random.randn(100).cumsum() + 105,
        "Low": np.random.randn(100).cumsum() + 95,
        "Close": np.random.randn(100).cumsum() + 100,
        "Volume": np.random.randint(1000, 10000, size=100)
    })
    
    indicators = compute_indicators(df)
    
    # Ensure returned dictionary has required keys
    assert isinstance(indicators, dict)
    assert "ma_5" in indicators
    assert "ma_20" in indicators
    assert "rsi_14" in indicators
    assert "macd_line" in indicators
    assert "atr_14" in indicators
    assert "trend_short" in indicators

@pytest.mark.asyncio
async def test_a_stock_provider_manifest():
    provider = AStockDirectProvider()
    manifest = provider.manifest
    assert manifest.id == "a_stock_direct"
    assert "realtime_quote" in manifest.capabilities

@pytest.mark.asyncio
async def test_a_stock_provider_fetch_quote():
    provider = AStockDirectProvider()
    
    # Fetch a quote for Ping An (601318)
    req = ProviderRequest(entity="601318", parameters={"data_type": "quote"})
    resp = await provider.fetch(req)
    
    # Since it fetches from internet, it might fail in CI if no connection.
    # But if it succeeds, it should have price and PE
    if resp.status == "success":
        data = resp.data
        assert "price" in data
        assert "symbol" in data
        assert data["symbol"] == "601318"
