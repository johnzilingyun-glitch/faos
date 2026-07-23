import logging
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List

from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderManifest, ProviderRequest, ProviderResponse

logger = logging.getLogger(__name__)

def calculate_rsi(data: pd.Series, periods=14):
    delta = data.diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    roll_up = up.ewm(com=periods - 1, adjust=False).mean()
    roll_down = down.ewm(com=periods - 1, adjust=False).mean().abs()
    rs = roll_up / roll_down
    return 100 - (100 / (1 + rs))

def calculate_macd(data: pd.Series, fast=12, slow=26, signal=9):
    exp1 = data.ewm(span=fast, adjust=False).mean()
    exp2 = data.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

POS_WORDS = ["surge", "jump", "record", "profit", "growth", "buy", "upgrade", "outperform", "expand", "dividend", "beat", "positive", "strong"]
NEG_WORDS = ["drop", "fall", "loss", "decline", "sell", "downgrade", "underperform", "shrink", "cut", "miss", "negative", "weak", "lawsuit", "penalty"]

def compute_sentiment(text: str) -> float:
    text = text.lower()
    pos_count = sum(1 for w in POS_WORDS if w in text)
    neg_count = sum(1 for w in NEG_WORDS if w in text)
    if pos_count == 0 and neg_count == 0:
        return 0.5
    
    score = (pos_count - neg_count) / (pos_count + neg_count)
    return round((score + 1) / 2, 2)

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
            
            # Helper to check if ticker is valid
            def is_valid_ticker(t):
                try:
                    return t.info.get("currentPrice") is not None or t.info.get("regularMarketPrice") is not None or t.info.get("previousClose") is not None
                except:
                    return False

            if not is_valid_ticker(ticker):
                # Fallback: strip Reuters/Bloomberg suffixes for US stocks
                if symbol.endswith(('.O', '.N', '.US')):
                    fallback_symbol = symbol.rsplit('.', 1)[0]
                    logger.warning(f"Ticker {symbol} not found. Trying fallback: {fallback_symbol}")
                    ticker = yf.Ticker(fallback_symbol)
                    if not is_valid_ticker(ticker):
                        raise Exception(f"Ticker {fallback_symbol} also not found.")
                else:
                    raise Exception(f"Ticker {symbol} not found or no price data.")
                    
            info = ticker.info
            
            # Try to get the most relevant price field
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0
            
            # Fetch 6 months of historical data for the chart
            hist = ticker.history(period="6mo")
            history_data = []
            if not hist.empty:
                for date, row in hist.iterrows():
                    history_data.append({
                        "time": date.strftime('%Y-%m-%d'),
                        "value": row["Close"],
                        "volume": row.get("Volume", 0)
                    })
                    
            # Additional Fundamental Data
            pe_ratio = info.get("trailingPE") or info.get("forwardPE")
            pb_ratio = info.get("priceToBook")
            ev_ebitda = info.get("enterpriseToEbitda")
            market_cap = info.get("marketCap")
            eps = info.get("trailingEps") or info.get("forwardEps")
            sector = info.get("sector")
            industry = info.get("industry")
            volume = info.get("volume") or info.get("regularMarketVolume")
            
            # Calculate Technical Indicators
            rsi_latest = None
            macd_latest = None
            if not hist.empty and len(hist) > 26:
                rsi = calculate_rsi(hist["Close"])
                macd, signal_line = calculate_macd(hist["Close"])
                rsi_latest = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
                macd_latest = float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else None

            # Fetch Comprehensive Financials
            def get_latest(df, key):
                if df is not None and not df.empty and key in df.index:
                    try:
                        return float(df.loc[key].iloc[0])
                    except:
                        pass
                return None
                
            inc = ticker.financials
            bs = ticker.balance_sheet
            cf = ticker.cashflow
            
            financials_summary = {
                "Total Revenue": get_latest(inc, "Total Revenue"),
                "Gross Profit": get_latest(inc, "Gross Profit"),
                "Operating Income": get_latest(inc, "Operating Income"),
                "Net Income": get_latest(inc, "Net Income"),
                "Total Assets": get_latest(bs, "Total Assets"),
                "Total Debt": get_latest(bs, "Total Debt"),
                "Operating Cash Flow": get_latest(cf, "Operating Cash Flow"),
                "Free Cash Flow": get_latest(cf, "Free Cash Flow")
            }
            
            # Fetch Alternative Data
            analyst_recommendations = None
            try:
                rec = ticker.recommendations
                if rec is not None and not rec.empty:
                    analyst_recommendations = rec.reset_index().to_dict(orient="records") if 'period' not in rec.columns else rec.to_dict(orient="records")
            except:
                pass

            # Fetch Estimates
            earnings_estimate = None
            try:
                est = getattr(ticker, "earnings_estimate", None)
                if est is not None and not est.empty:
                    earnings_estimate = est.reset_index().to_dict(orient="records")
            except:
                pass

            revenue_estimate = None
            try:
                est = getattr(ticker, "revenue_estimate", None)
                if est is not None and not est.empty:
                    revenue_estimate = est.reset_index().to_dict(orient="records")
            except:
                pass
            
            data = {
                "symbol": symbol,
                "price": price,
                "volume": volume,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "ev_ebitda": ev_ebitda,
                "market_cap": market_cap,
                "eps": eps,
                "sector": sector,
                "industry": industry,
                "technical_indicators": {
                    "RSI_14": rsi_latest,
                    "MACD": macd_latest
                },
                "financials_summary": financials_summary,
                "analyst_recommendations": analyst_recommendations,
                "analyst_estimates": {
                    "earnings": earnings_estimate,
                    "revenue": revenue_estimate
                },
                "history": history_data,
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
                if "content" in item:
                    content = item["content"]
                    title = content.get("title", "")
                    provider = content.get("provider", {})
                    publisher = provider.get("displayName", "")
                else:
                    title = item.get("title", "")
                    publisher = item.get("publisher", "")
                    
                results.append({
                    "title": title,
                    "publisher": publisher,
                    "sentiment": compute_sentiment(title),
                    "source": "YFinanceNewsProvider"
                })
                
            return ProviderResponse(status="success", data=results)
        except Exception as e:
            logger.error(f"Error fetching news for {symbol}: {e}")
            return ProviderResponse(status="failed", error=str(e))
