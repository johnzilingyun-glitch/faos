"""
Polars Indicator Engine — High performance technical indicator calculation.

Replaces Pandas-based calculations in yfinance_impl.py. Polars is 5-10x faster
for time-series operations.
"""

import logging
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

def compute_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute technical indicators using Polars for high performance.
    Expects a pandas DataFrame with Date, Open, High, Low, Close, Volume.
    Returns a dictionary of the latest indicator values.

    Polars is an optional, undeclared dependency: if it is not installed the
    server still starts and the quote provider degrades gracefully (no extra
    technical indicators) instead of crashing at import time.
    """
    if df is None or df.empty or len(df) < 30:
        return {}

    try:
        import polars as pl
    except ImportError:
        logger.warning(
            "polars not installed; skipping technical indicators. "
            "Install with: pip install polars"
        )
        return {}

    try:
        # Convert pandas to polars (reset index if Date is index)
        if "Date" not in df.columns and isinstance(df.index, pd.DatetimeIndex):
            pdf = df.reset_index()
        else:
            pdf = df.copy()
            
        pldf = pl.from_pandas(pdf)
        
        # Ensure we have required columns
        required = ["Close", "High", "Low"]
        if not all(col in pldf.columns for col in required):
            return {}
            
        # Calculate moving averages
        pldf = pldf.with_columns([
            pl.col("Close").rolling_mean(window_size=5).alias("ma_5"),
            pl.col("Close").rolling_mean(window_size=10).alias("ma_10"),
            pl.col("Close").rolling_mean(window_size=20).alias("ma_20"),
            pl.col("Close").rolling_mean(window_size=60).alias("ma_60"),
        ])
        
        # Calculate RSI (14)
        # Using Wilder's smoothing for RSI
        delta = pl.col("Close").diff()
        up = pl.when(delta > 0).then(delta).otherwise(0)
        down = pl.when(delta < 0).then(delta.abs()).otherwise(0)
        
        # We use a simple EMA approximation for Polars
        alpha = 1.0 / 14.0
        pldf = pldf.with_columns([
            up.ewm_mean(alpha=alpha, adjust=False).alias("rs_up"),
            down.ewm_mean(alpha=alpha, adjust=False).alias("rs_down")
        ])
        
        rs = pl.col("rs_up") / pl.col("rs_down")
        pldf = pldf.with_columns(
            pl.when(pl.col("rs_down") == 0).then(100)
            .otherwise(100 - (100 / (1 + rs)))
            .alias("rsi_14")
        )
        
        # Calculate MACD (12, 26, 9)
        macd_fast = pl.col("Close").ewm_mean(span=12, adjust=False)
        macd_slow = pl.col("Close").ewm_mean(span=26, adjust=False)
        pldf = pldf.with_columns((macd_fast - macd_slow).alias("macd_line"))
        pldf = pldf.with_columns(
            pl.col("macd_line").ewm_mean(span=9, adjust=False).alias("macd_signal")
        )
        pldf = pldf.with_columns(
            (pl.col("macd_line") - pl.col("macd_signal")).alias("macd_hist")
        )
        
        # Calculate ATR (14)
        tr1 = (pl.col("High") - pl.col("Low")).abs()
        tr2 = (pl.col("High") - pl.col("Close").shift(1)).abs()
        tr3 = (pl.col("Low") - pl.col("Close").shift(1)).abs()
        
        true_range = pl.max_horizontal([tr1, tr2, tr3])
        pldf = pldf.with_columns(
            true_range.rolling_mean(window_size=14).alias("atr_14")
        )
        
        # Extract latest row
        latest = pldf.row(-1, named=True)
        
        # Clean up numpy types for JSON serialization
        import math
        def _clean_val(v):
            if v is None or math.isnan(v): return None
            return float(v)
            
        return {
            "price": _clean_val(latest.get("Close")),
            "ma_5": _clean_val(latest.get("ma_5")),
            "ma_10": _clean_val(latest.get("ma_10")),
            "ma_20": _clean_val(latest.get("ma_20")),
            "ma_60": _clean_val(latest.get("ma_60")),
            "rsi_14": _clean_val(latest.get("rsi_14")),
            "macd_line": _clean_val(latest.get("macd_line")),
            "macd_signal": _clean_val(latest.get("macd_signal")),
            "macd_hist": _clean_val(latest.get("macd_hist")),
            "atr_14": _clean_val(latest.get("atr_14")),
            "trend_short": "bullish" if latest.get("Close") > latest.get("ma_20") else "bearish",
            "trend_mid": "bullish" if latest.get("Close") > latest.get("ma_60") else "bearish",
        }
    except Exception as e:
        logger.warning(f"Polars indicator calculation failed: {e}")
        return {}
