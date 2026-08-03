"""
A-Share Direct Provider — Primary data source for China A-Shares.

Directly connects to HTTP APIs (Tencent, EastMoney, Sina)
without intermediate wrappers like API.
"""

import asyncio
import logging
import urllib.request
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

import requests
import pandas as pd

from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderRequest, ProviderResponse, ProviderManifest
from faos.services.provider.polars_indicators import compute_indicators

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

def _clean_symbol(symbol: str) -> str:
    """Normalize various symbol formats to pure code."""
    s = symbol.strip().upper()
    if s.endswith(".HK") or s.startswith("HK"):
        s = s.replace(".HK", "").replace("HK", "")
        s = s.lstrip("0") or "0"
        return s.zfill(5)
        
    for suffix in (".SH", ".SS", ".SZ", ".BJ"):
        s = s.replace(suffix, "")
    for prefix in ("SH", "SZ", "BJ"):
        if s.startswith(prefix) and len(s) > 2:
            s = s[2:]
    return s[:6]

def _get_prefix(code: str) -> str:
    """Code → market prefix (sh/sz/bj/hk)."""
    if len(code) == 5:
        return "hk"
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    else:
        return "sz"

def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure standard column names and types for OHLCV data."""
    if df.empty:
        return df
    
    col_map = {
        "date": "Date", "Date": "Date",
        "open": "Open", "Open": "Open",
        "high": "High", "High": "High",
        "low": "Low",   "Low": "Low",
        "close": "Close", "Close": "Close",
        "volume": "Volume", "Volume": "Volume"
    }
    df = df.rename(columns=col_map)
    
    # Ensure datetime index
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    # Ensure numeric types
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            
    df = df.sort_index()
    return df


def _compute_technical_indicators(df: pd.DataFrame) -> dict:
    """
    Compute technical indicators using Polars for high performance.
    """
    try:
        return compute_indicators(df)
    except Exception as e:
        logger.debug(f"Technical indicator computation failed: {e}")
        return {}



class AStockDirectProvider(BaseProvider):
    """
    Primary A-Share data provider using direct HTTP APIs.
    No API dependency — connects directly to Tencent, EastMoney, Sina.
    """

    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="a_stock_direct",
            name="A-Share Direct Provider",
            category="market",
            capabilities=["realtime_quote", "history", "financials", "industry_valuation"],
            supported_parameters=["period", "interval", "industry_name"],
            priority=200, # Higher priority than yfinance for A-shares
            description="Direct connection to Tencent and EastMoney for A-Shares"
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        """Unified fetch interface — returns quote + history + financials for full analysis."""
        data_type = request.parameters.get("data_type", "quote")
        
        try:
            if data_type == "quote":
                data = await self.get_quote(request.entity)
                if data:
                    # Also fetch K-line history for chart & technical analysis
                    try:
                        hist_df = await self.get_history(request.entity, period="6mo")
                        if not hist_df.empty:
                            data["history"] = [
                                {"time": r["Date"].strftime("%Y-%m-%d"), "value": r["Close"], "volume": r.get("Volume", 0)}
                                for r in hist_df.reset_index().to_dict(orient="records")
                                if "Date" in r or "time" in r
                            ]
                            # Fallback: build from DataFrame columns if "Date" field name differs
                            if not data.get("history"):
                                cols = hist_df.reset_index().columns.tolist()
                                date_col = next((c for c in cols if c.lower() in ("date", "time")), cols[0])
                                hist_rows = hist_df.reset_index().to_dict(orient="records")
                                data["history"] = [
                                    {"time": str(r.get(date_col, "")), "value": r.get("Close", r.get("close", 0)), "volume": r.get("Volume", r.get("volume", 0))}
                                    for r in hist_rows
                                ]
                    except Exception as e:
                        logger.debug(f"History fetch (non-critical) failed: {e}")

                    # Compute technical indicators from the history data
                    if not hist_df.empty:
                        try:
                            indicators = _compute_technical_indicators(hist_df)
                            # Pass current price for BB band positioning
                            indicators["price"] = data.get("price")
                            data["technical_indicators"] = indicators
                        except Exception as e:
                            logger.debug(f"Technical indicators (non-critical) failed: {e}")

                    # Also fetch financial statements for fundamental analysis
                    try:
                        fin_data = await self.get_financials(request.entity)
                        if fin_data:
                            data["financials"] = fin_data
                    except Exception as e:
                        logger.debug(f"Financials fetch (non-critical) failed: {e}")

                    return ProviderResponse(status="success", data=data)
            elif data_type == "history":
                period = request.parameters.get("period", "3mo")
                interval = request.parameters.get("interval", "1d")
                df = await self.get_history(request.entity, period, interval)
                if not df.empty:
                    return ProviderResponse(status="success", data=df)
            elif data_type == "industry_valuation":
                industry_name = request.parameters.get("industry_name")
                if industry_name:
                    data = await fetch_industry_valuation(industry_name)
                    if data:
                        return ProviderResponse(status="success", data=data)
            
            return ProviderResponse(status="failed", error=f"No data found for {request.entity} ({data_type})")
        except Exception as e:
            logger.error(f"[AStockDirectProvider] Fetch failed: {e}")
            return ProviderResponse(status="failed", error=str(e))

    async def get_history(self, symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
        """Fetch K-line history from Tencent web API."""
        code = _clean_symbol(symbol)
        prefix = _get_prefix(code)
        qt_symbol = f"{prefix}{code}"

        period_days = {
            "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "max": 3650,
        }
        days = period_days.get(period, 90)

        kline_type = "day"
        if interval == "1wk": kline_type = "week"
        elif interval == "1mo": kline_type = "month"
        elif interval == "1y": kline_type = "year"
        elif interval == "15m": kline_type = "m15"
        elif interval in ("1h", "60m"): kline_type = "m60"

        from datetime import timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        is_min = interval in ("15m", "1h", "60m")
        if is_min:
            url = "https://ifzq.gtimg.cn/appstock/app/kline/mkline"
            params = {"param": f"{qt_symbol},{kline_type},,640"}
        else:
            url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                "_var": "kline_dayqfq",
                "param": f"{qt_symbol},{kline_type},{start_date},{end_date},640,qfq",
            }

        loop = asyncio.get_event_loop()
        try:
            def _fetch():
                r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=10)
                text = r.text
                json_str = text.split("=", 1)[1] if "=" in text else text
                return json.loads(json_str)

            d = await loop.run_in_executor(None, _fetch)
            stock_data = d.get("data", {}).get(qt_symbol, {})

            if is_min:
                klines = stock_data.get(kline_type, [])
            else:
                klines = stock_data.get(f"qfq{kline_type}", stock_data.get(kline_type, []))
            
            if not klines:
                return pd.DataFrame()

            rows = []
            for k in klines:
                if len(k) >= 6:
                    date_val = k[0]
                    if is_min and len(date_val) == 12:
                        date_val = f"{date_val[:4]}-{date_val[4:6]}-{date_val[6:8]} {date_val[8:10]}:{date_val[10:12]}:00"
                    
                    rows.append({
                        "date": date_val,
                        "open": float(k[1]),
                        "close": float(k[2]),
                        "high": float(k[3]),
                        "low": float(k[4]),
                        "volume": float(k[5]),
                    })

            df = pd.DataFrame(rows)
            return _normalize_ohlcv(df)
        except Exception as e:
            logger.warning(f"[AStockDirectProvider] Tencent kline failed for {code}: {e}")
            return pd.DataFrame()

    async def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Real-time quote from Tencent Finance API."""
        code = _clean_symbol(symbol)
        prefix = _get_prefix(code)
        qt_symbol = f"{prefix}{code}"

        loop = asyncio.get_event_loop()
        try:
            def _fetch():
                url = f"https://qt.gtimg.cn/q={qt_symbol}"
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "Mozilla/5.0")
                resp = urllib.request.urlopen(req, timeout=10)
                return resp.read().decode("gbk")

            data = await loop.run_in_executor(None, _fetch)
            vals = data.split('"')[1].split("~")
            if len(vals) < 53:
                return None

            return {
                "symbol": code,
                "name": vals[1],
                "price": float(vals[3]) if vals[3] else 0.0,
                "open": float(vals[5]) if vals[5] else 0.0,
                "high": float(vals[33]) if vals[33] else 0.0,
                "low": float(vals[34]) if vals[34] else 0.0,
                "last_close": float(vals[4]) if vals[4] else 0.0,
                "change": float(vals[31]) if vals[31] else 0.0,
                "change_pct": float(vals[32]) if vals[32] else 0.0,
                "volume": float(vals[36]) if vals[36] else 0.0,
                "amount": float(vals[37]) * 10000 if vals[37] else 0.0,
                "market_cap": float(vals[44]) * 1e8 if vals[44] else None,
                "pe_ttm": float(vals[39]) if vals[39] else None,
                "pb": float(vals[46]) if vals[46] else None,
                "turnover_pct": float(vals[38]) if vals[38] else None,
                "source": "AStockDirectProvider",
            }
        except Exception as e:
            logger.warning(f"[AStockDirectProvider] Quote failed for {code}: {e}")
            return None

    async def get_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch latest financial statements via akshare (EastMoney datacenter).
        Returns income statement, balance sheet, cash flow, and key indicators.
        """
        code = _clean_symbol(symbol)
        loop = asyncio.get_event_loop()

        def _fetch():
            import akshare as ak
            result: Dict[str, Any] = {
                "summary": {},
                "source": "EastMoney via akshare",
            }
            try:
                # Fetch key financial indicators (annual)
                df = ak.stock_financial_abstract_ths(symbol=code, indicator="按年度")
                if df is not None and not df.empty:
                    # Get the latest row
                    latest = df.iloc[-1].to_dict() if len(df) > 0 else {}
                    result["indicators_raw"] = latest
                    # Map to standard names
                    _MAP = {
                        "营业总收入": "revenue",
                        "净利润": "net_profit",
                        "扣非净利润": "deducted_net_profit",
                        "基本每股收益": "eps",
                        "每股净资产": "bvps",
                        "每股经营现金流": "ocf_per_share",
                        "销售毛利率": "gross_margin_pct",
                        "销售净利率": "net_margin_pct",
                        "净资产收益率": "roe",
                        "净资产收益率-摊薄": "roe_diluted",
                        "营业总收入同比增长率": "revenue_yoy",
                        "净利润同比增长率": "net_profit_yoy",
                        "扣非净利润同比增长率": "deducted_net_profit_yoy",
                        "资产负债率": "debt_ratio",
                        "产权比率": "debt_to_equity",
                        "流动比率": "current_ratio",
                        "速动比率": "quick_ratio",
                        "存货周转率": "inventory_turnover",
                        "应收账款周转天数": "receivable_days",
                        "营业周期": "operating_cycle",
                    }
                    for cn, en in _MAP.items():
                        if cn in latest and latest[cn] is not None:
                            result["summary"][en] = latest[cn]
            except Exception as e:
                logger.debug(f"akshare financial indicators failed: {e}")

            try:
                # Fetch cash flow data (annual)
                df_cf = ak.stock_financial_cash_flow(symbol=code)
                if df_cf is not None and not df_cf.empty:
                    # Get latest annual
                    latest_cf = df_cf.iloc[-1].to_dict() if len(df_cf) > 0 else {}
                    _CF_MAP = {
                        "经营活动产生的现金流量净额": "operating_cashflow",
                        "投资活动产生的现金流量净额": "investing_cashflow",
                        "筹资活动产生的现金流量净额": "financing_cashflow",
                        "购建固定资产、无形资产和其他长期资产支付的现金": "capex",
                    }
                    for cn, en in _CF_MAP.items():
                        if cn in latest_cf and latest_cf[cn] is not None:
                            result["summary"][en] = latest_cf[cn]
            except Exception as e:
                logger.debug(f"akshare cash flow failed: {e}")

            # Calculate derived metrics
            s = result["summary"]
            if "ocf_per_share" in s and "eps" in s:
                try:
                    s["ocf_to_eps_ratio"] = float(s["ocf_per_share"]) / float(s["eps"])
                except (ZeroDivisionError, TypeError, ValueError):
                    pass
            # debt_to_equity is already from 产权比率 in the raw data

            return result if result["summary"] else None

        try:
            data = await loop.run_in_executor(None, _fetch)
            return data
        except Exception as e:
            logger.warning(f"[AStockDirectProvider] Financials failed for {code}: {e}")
            return None

    def _extract_financial_summary(self, fin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deprecated: summary is now built in get_financials directly."""
        return fin_data.get("summary", {})


async def fetch_industry_valuation(industry_name: str) -> Dict[str, Any]:
    """Fetch industry valuation benchmarks from EastMoney datacenter."""
    def _fetch_page(page_number: int) -> List[Dict]:
        url = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
        params = {
            "reportName": "RPT_VALUEANALYSIS_DET",
            "columns": "ALL",
            "filter": f'(BOARD_NAME="{industry_name}")',
            "pageNumber": str(page_number),
            "pageSize": "500",
            "sortColumns": "",
            "sortTypes": "-1",
            "source": "WEB",
            "client": "PC",
        }
        try:
            r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=30)
            d = r.json()
            if d.get("result") and d["result"].get("data"):
                return d["result"]["data"]
        except Exception:
            pass
        return []

    try:
        rows = await asyncio.to_thread(_fetch_page, 1)
        if not rows:
            return {}
        
        pe_vals, pb_vals = [], []
        for row in rows:
            try:
                pe = row.get("PE_TTM")
                if pe is not None and float(pe) > 0:
                    pe_vals.append(float(pe))
            except (TypeError, ValueError):
                pass
            try:
                pb = row.get("PB_MRQ")
                if pb is not None and float(pb) > 0:
                    pb_vals.append(float(pb))
            except (TypeError, ValueError):
                pass

        def _stats(vals: List[float]):
            if not vals:
                return None, None
            sorted_vals = sorted(vals)
            n = len(sorted_vals)
            mean = sum(sorted_vals) / n
            if n % 2 == 0:
                med = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
            else:
                med = sorted_vals[n // 2]
            return mean, med

        out: Dict[str, Any] = {}
        pe_mean, pe_med = _stats(pe_vals)
        if pe_mean is not None:
            out["pe_avg"] = round(pe_mean, 2)
            out["pe_med"] = round(pe_med, 2)

        pb_mean, pb_med = _stats(pb_vals)
        if pb_mean is not None:
            out["pb_avg"] = round(pb_mean, 2)
            out["pb_med"] = round(pb_med, 2)

        return out
    except Exception as e:
        logger.warning(f"[IndustryValuation] Failed for {industry_name}: {e}")
        return {}
