import os
import sqlite3
import json
import logging
import re
import threading
import time
from typing import List, Dict, Any
import httpx
import yfinance as yf
from faos.services.history import history_storage

logger = logging.getLogger("faos.watchlist")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "faos_history.db")

DEFAULT_WATCHLIST = ["AAPL", "TSLA", "NVDA", "MU", "MSFT", "宝丰能源"]


def _looks_like_ticker(symbol: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_.-]+", symbol))


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _looks_like_cjk_market_symbol(symbol: str) -> bool:
    return bool(re.fullmatch(r"\d{4,6}(?:\.(?:SZ|SS|HK))?", symbol.upper()))


def _normalize_watchlist_symbol(symbol: str) -> str:
    stripped = symbol.strip()
    if not stripped:
        return stripped
    if _contains_cjk(stripped):
        return stripped
    return stripped.upper()


def _candidate_suffixes(symbol: str) -> List[str]:
    if symbol.isdigit() and len(symbol) == 6:
        if symbol.startswith(("6", "5")):
            return [f"{symbol}.SS", f"{symbol}.SZ"]
        return [f"{symbol}.SZ", f"{symbol}.SS"]
    if symbol.isdigit() and len(symbol) == 5:
        return [f"{symbol}.HK"]
    return [symbol]


def _extract_symbol_candidates(text: str) -> List[str]:
    if not text:
        return []

    candidates: List[str] = []
    patterns = [
        r"\(([A-Z]{1,6})\)",
        r"\((\d{4,6})\)",
        r"\b\d{6}\.(?:SZ|SS)\b",
        r"\b\d{5}\.HK\b",
        r"\b\d{4}\.HK\b",
        r"\b\d{1,5}\.US\b",
        r"\b\d{6}\b",
        r"\b\d{5}\b",
    ]
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            normalized = match.upper()
            if normalized in {"ZH", "US", "HK", "SZ", "SS", "NYSE", "NASDAQ"}:
                continue
            if len(normalized) == 1 and normalized.isalpha():
                continue
            if normalized.isdigit() and len(normalized) == 4 and 1900 <= int(normalized) <= 2099:
                continue
            if normalized not in candidates:
                candidates.append(normalized)
    return candidates

class WatchlistService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._price_cache: Dict[str, Dict[str, Any]] = {}
        self._resolved_symbol_cache: Dict[str, Dict[str, Any]] = {}
        self._last_refresh: float = 0
        self._refresh_interval = 600  # 10 minutes
        self._refresh_lock = threading.Lock()
        self._init_db()
        # Initial price fetch in background
        threading.Thread(target=self._refresh_prices, daemon=True).start()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_watchlist (
                        symbol TEXT PRIMARY KEY,
                        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS watchlist_symbol_aliases (
                        input_symbol TEXT PRIMARY KEY,
                        resolved_symbol TEXT NOT NULL,
                        source TEXT NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

                # Seed initial watchlist if empty
                cursor.execute("SELECT COUNT(*) as cnt FROM user_watchlist")
                if cursor.fetchone()["cnt"] == 0:
                    for sym in DEFAULT_WATCHLIST:
                        cursor.execute("INSERT OR IGNORE INTO user_watchlist (symbol) VALUES (?)", (sym,))
                    conn.commit()
            logger.info("SQLite Watchlist DB initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Watchlist DB: {e}")

    def _get_alias(self, symbol: str) -> str | None:
        cached = self._resolved_symbol_cache.get(symbol)
        if cached and cached.get("resolved_symbol"):
            return cached["resolved_symbol"]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT resolved_symbol, source FROM watchlist_symbol_aliases WHERE input_symbol = ?",
                    (symbol,)
                )
                row = cursor.fetchone()
                if row:
                    self._resolved_symbol_cache[symbol] = {
                        "resolved_symbol": row["resolved_symbol"],
                        "source": row["source"],
                    }
                    return row["resolved_symbol"]
        except Exception as e:
            logger.debug(f"Failed to read symbol alias cache for {symbol}: {e}")

        return None

    def _save_alias(self, input_symbol: str, resolved_symbol: str, source: str) -> None:
        if not input_symbol or not resolved_symbol:
            return

        self._resolved_symbol_cache[input_symbol] = {
            "resolved_symbol": resolved_symbol,
            "source": source,
        }

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO watchlist_symbol_aliases (input_symbol, resolved_symbol, source, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(input_symbol) DO UPDATE SET
                        resolved_symbol = excluded.resolved_symbol,
                        source = excluded.source,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (input_symbol, resolved_symbol, source),
                )
                conn.commit()
        except Exception as e:
            logger.debug(f"Failed to persist symbol alias for {input_symbol}: {e}")

    def _is_valid_quote(self, symbol: str) -> bool:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return any([
                info.get("currentPrice") is not None,
                info.get("regularMarketPrice") is not None,
                info.get("previousClose") is not None,
            ])
        except Exception:
            return False

    def _resolve_from_web_search(self, symbol: str) -> str | None:
        if re.fullmatch(r"[A-Za-z]{2,5}", symbol):
            queries = [
                symbol,
                f"{symbol} stock ticker",
                f"{symbol} company stock",
                f"{symbol} stock price quote",
                f"{symbol} 股票代码 ticker",
                f"{symbol} 股票",
                f"{symbol} 公司",
            ]
        else:
            queries = [
                f"{symbol} 股票代码 ticker",
                f"{symbol} stock ticker",
                f"{symbol} company stock",
            ]
            if _looks_like_ticker(symbol) and len(symbol) <= 5:
                queries.extend([
                    symbol,
                    f"{symbol} 股票",
                    f"{symbol} 公司",
                ])
        candidates: List[str] = []
        search_payloads = []

        tavily_key = os.environ.get("TAVILY_API_KEY", "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")
        serper_key = os.environ.get("SERPER_API_KEY", "ce54c5b01ef640bc086f96b4c511aef7fcb56c66")
        jina_key = os.environ.get("JINA_API_KEY", "jina_536c44d451074d0f82a5dcd1967f01banpUgiyNUWAaFEoEaNoIJpxj_OJw_")

        with httpx.Client(timeout=10.0) as client:
            for query in queries:
                search_payloads = []
                if tavily_key:
                    search_payloads.append(("https://api.tavily.com/search", {
                        "api_key": tavily_key,
                        "query": query,
                        "search_depth": "basic",
                        "include_answer": False,
                        "max_results": 5,
                    }, "post", "Tavily"))
                if serper_key:
                    search_payloads.append(("https://google.serper.dev/search", {
                        "q": query,
                    }, "post", "Serper"))
                if jina_key:
                    search_payloads.append((f"https://s.jina.ai/{query}", None, "get", "Jina"))

                for url, payload, method, source in search_payloads:
                    try:
                        if method == "post":
                            headers = {"Content-Type": "application/json"}
                            if source == "Serper":
                                headers["X-API-KEY"] = serper_key
                            resp = client.post(url, json=payload, headers=headers)
                        else:
                            headers = {"Authorization": f"Bearer {jina_key}", "Accept": "application/json"}
                            resp = client.get(url, headers=headers)
                        resp.raise_for_status()
                        data = resp.json()
                        if source == "Tavily":
                            items = data.get("results", [])
                        elif source == "Serper":
                            items = data.get("organic", [])
                        else:
                            items = data.get("data", [])

                        for item in items[:5]:
                            blobs = [
                                str(item.get("title", "")),
                                str(item.get("url", "")),
                                str(item.get("content", item.get("snippet", ""))),
                                str(item.get("description", "")),
                            ]
                            for blob in blobs:
                                candidates.extend(_extract_symbol_candidates(blob))
                        if candidates:
                            break
                    except Exception as e:
                        logger.debug(f"Search resolver {source} failed for {symbol} via '{query}': {e}")
                if candidates:
                    break

        for candidate in candidates:
            for resolved in _candidate_suffixes(candidate):
                if self._is_valid_quote(resolved):
                    return resolved

        return None

    def _resolve_quote_symbol(self, symbol: str) -> str:
        normalized = _normalize_watchlist_symbol(symbol)
        if not normalized:
            return normalized

        cached = self._get_alias(normalized)
        if cached and self._is_valid_quote(cached):
            if re.fullmatch(r"[A-Z]{2,5}", normalized):
                if cached != normalized and len(cached) > len(normalized):
                    return cached
            elif not (_contains_cjk(normalized) and not _looks_like_cjk_market_symbol(cached)):
                return cached

        # Short alphabetic inputs are often abbreviations or ambiguous tickers,
        # so ask search first before accepting the bare symbol.
        if re.fullmatch(r"[A-Z]{2,5}", normalized):
            resolved = self._resolve_from_web_search(normalized)
            if resolved:
                self._save_alias(normalized, resolved, "web-search")
                return resolved

        direct_candidates = [normalized, normalized.upper()]
        for candidate in direct_candidates:
            if self._is_valid_quote(candidate):
                self._save_alias(normalized, candidate, "direct")
                return candidate

        for candidate in _candidate_suffixes(normalized):
            if candidate != normalized and self._is_valid_quote(candidate):
                self._save_alias(normalized, candidate, "format-heuristic")
                return candidate

        if not _looks_like_ticker(normalized):
            resolved = self._resolve_from_web_search(normalized)
            if resolved:
                self._save_alias(normalized, resolved, "web-search")
                return resolved

        self._save_alias(normalized, normalized, "unresolved")
        return normalized

    def _get_symbols(self) -> List[str]:
        """Get all symbols from the watchlist table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT symbol FROM user_watchlist ORDER BY rowid ASC")
                return [r["symbol"] for r in cursor.fetchall()]
        except Exception:
            return DEFAULT_WATCHLIST

    def _refresh_prices(self):
        """Fetch real-time prices for all watchlist symbols via yfinance."""
        with self._refresh_lock:
            symbols = self._get_symbols()
            logger.info(f"Refreshing real-time prices for {len(symbols)} watchlist symbols...")
            for sym in symbols:
                try:
                    yf_sym = self._resolve_quote_symbol(sym)
                    ticker = yf.Ticker(yf_sym)
                    info = ticker.info
                    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0.0
                    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
                    if prev_close and prev_close > 0:
                        change_pct = round((price - prev_close) / prev_close * 100, 2)
                    else:
                        change_pct = 0.0
                    self._price_cache[sym] = {
                        "current_price": round(price, 2),
                        "change_pct": change_pct,
                        "resolved_symbol": yf_sym,
                        "updated_at": time.time()
                    }
                    logger.info(f"  {sym} ({yf_sym}): ${price:.2f} ({change_pct:+.2f}%)")
                except Exception as e:
                    logger.warning(f"  Failed to fetch price for {sym}: {e}")
                    # Keep stale cache if available
            self._last_refresh = time.time()
            logger.info("Price refresh complete.")

    def start_background_refresh(self):
        """Start the background thread that refreshes prices every 10 minutes."""
        def _loop():
            while True:
                time.sleep(self._refresh_interval)
                try:
                    self._refresh_prices()
                except Exception as e:
                    logger.error(f"Background price refresh error: {e}")
        t = threading.Thread(target=_loop, daemon=True)
        t.start()
        logger.info(f"Background price refresh started (interval={self._refresh_interval}s)")

    def force_refresh(self):
        """Force an immediate price refresh (called from API)."""
        threading.Thread(target=self._refresh_prices, daemon=True).start()

    def get_last_refresh_time(self) -> float:
        return self._last_refresh

    def list_watchlist(self) -> List[Dict[str, Any]]:
        """
        Retrieves user watchlist enriched with current live price, 24h change %,
        latest AI verdict, analysis count, and last analyzed timestamp from SQLite history.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT symbol, added_at FROM user_watchlist ORDER BY rowid ASC")
                rows = cursor.fetchall()
                symbols = [r["symbol"] for r in rows]
        except Exception as e:
            logger.error(f"Error reading watchlist: {e}")
            symbols = DEFAULT_WATCHLIST

        history_records = history_storage.list_records(limit=200)

        # Map history per symbol
        symbol_history: Dict[str, List[Dict[str, Any]]] = {}
        for rec in history_records:
            sym = rec.get("symbol") or "Asset"
            if sym not in symbol_history:
                symbol_history[sym] = []
            symbol_history[sym].append(rec)

        result = []
        for sym in symbols:
            recs = symbol_history.get(sym, [])
            analysis_count = len(recs)
            last_analyzed = recs[0]["timestamp"] if recs else "未分析"
            latest_decision = recs[0]["decision"]["pm"]["decision"] if (recs and recs[0].get("decision") and recs[0]["decision"].get("pm")) else "HOLD"

            # Use cached real-time price data
            cached = self._price_cache.get(sym)
            if cached:
                current_price = cached["current_price"]
                change_pct = cached["change_pct"]
            else:
                current_price = 0.0
                change_pct = 0.0

            result.append({
                "symbol": sym,
                "current_price": current_price,
                "change_pct": change_pct,
                "latest_verdict": latest_decision,
                "analysis_count": analysis_count,
                "last_analyzed": last_analyzed
            })

        return result

    def add_symbol(self, symbol: str) -> bool:
        """Add a stock symbol to watchlist."""
        sym = _normalize_watchlist_symbol(symbol)
        if not sym: return False
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO user_watchlist (symbol) VALUES (?)", (sym,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding symbol {symbol}: {e}")
            return False

    def remove_symbol(self, symbol: str) -> bool:
        """Remove a stock symbol from watchlist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_watchlist WHERE symbol = ?", (symbol,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error removing symbol {symbol}: {e}")
            return False

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Returns overall user analysis activity statistics."""
        history_records = history_storage.list_records(limit=200)
        watchlist = self.list_watchlist()

        total_analyses = len(history_records)
        total_watchlist = len(watchlist)

        bull_count = sum(1 for item in watchlist if item["latest_verdict"] == "BUY")
        bear_count = sum(1 for item in watchlist if item["latest_verdict"] == "SELL")
        hold_count = total_watchlist - bull_count - bear_count

        bullish_ratio = round((bull_count / total_watchlist * 100), 1) if total_watchlist > 0 else 0.0

        # Most analyzed stock
        most_analyzed = max(watchlist, key=lambda x: x["analysis_count"]) if watchlist else {"symbol": "--", "analysis_count": 0}

        return {
            "total_analyses": total_analyses,
            "total_watchlist": total_watchlist,
            "bull_count": bull_count,
            "bear_count": bear_count,
            "hold_count": hold_count,
            "bullish_ratio": bullish_ratio,
            "most_analyzed_symbol": most_analyzed["symbol"],
            "most_analyzed_count": most_analyzed["analysis_count"]
        }

watchlist_service = WatchlistService()
