import re
import time
import logging
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

import yfinance as yf

from faos.services.history import history_storage
from faos.services.portfolio import watchlist_service

logger = logging.getLogger("faos.backtest")

# Directional keyword lexicon for per-analyst stance attribution
BULL_WORDS = [
    "看多", "买入", "做多", "上涨", "增长", "利好", "突破", "强势", "低估", "增持",
    "bullish", "buy", "upside", "outperform", "strong", "growth", "positive", "beat", "upgrade"
]
BEAR_WORDS = [
    "看空", "卖出", "做空", "下跌", "回落", "利空", "风险", "疲软", "高估", "减持",
    "bearish", "sell", "downside", "underperform", "weak", "decline", "negative", "miss", "downgrade"
]

# Number of forward trading days used to evaluate each decision
HOLD_WINDOW = 5
# Neutral band (%) within which a HOLD call is considered correct
HOLD_BAND_PCT = 3.0
# Cache TTL for the full backtest result (seconds)
CACHE_TTL = 300


def _parse_decision_date(timestamp: str) -> Optional[date]:
    """Parse the locale-formatted timestamp saved by the frontend into a date."""
    if not timestamp:
        return None

    # Year-first, e.g. "2026/7/22 21:01:43" or "2026-07-22 09:15:00"
    m = re.search(r"(\d{4})\D+(\d{1,2})\D+(\d{1,2})", timestamp)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    # Month-first, e.g. "7/22/2026, 9:01:43 PM"
    m = re.search(r"(\d{1,2})\D+(\d{1,2})\D+(\d{4})", timestamp)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(1)), int(m.group(2)))
        except ValueError:
            pass

    return None


def _stance_from_text(text: str) -> int:
    """Return +1 bullish, -1 bearish, 0 neutral based on keyword balance."""
    if not text:
        return 0
    low = text.lower()
    bull = sum(low.count(w.lower()) for w in BULL_WORDS)
    bear = sum(low.count(w.lower()) for w in BEAR_WORDS)
    if bull > bear:
        return 1
    if bear > bull:
        return -1
    return 0


class AccuracyBacktester:
    """
    Evaluates prediction accuracy of past AI decisions against REAL market price
    movements fetched from Yahoo Finance (T+N forward returns).
    """

    def __init__(self):
        self._symbol_cache: Dict[str, Optional[str]] = {}
        self._price_cache: Dict[str, Any] = {}
        self._result_cache: Optional[Dict[str, Any]] = None
        self._result_cache_ts: float = 0.0
        logger.info("AccuracyBacktester initialized (real price-based)")

    # ── Price helpers ────────────────────────────────────────
    def _resolve_symbol(self, symbol: str) -> Optional[str]:
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]
        try:
            resolved = watchlist_service._resolve_quote_symbol(symbol)
        except Exception as e:
            logger.warning(f"Symbol resolution failed for {symbol}: {e}")
            resolved = symbol
        self._symbol_cache[symbol] = resolved
        return resolved

    def _get_history(self, yf_symbol: str, start: date, end: date):
        cache_key = f"{yf_symbol}:{start.isoformat()}:{end.isoformat()}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]
        try:
            hist = yf.Ticker(yf_symbol).history(
                start=start.isoformat(),
                end=end.isoformat(),
                auto_adjust=True,
            )
        except Exception as e:
            logger.warning(f"History fetch failed for {yf_symbol}: {e}")
            hist = None
        self._price_cache[cache_key] = hist
        return hist

    def _forward_return(self, symbol: str, decision_dt: date) -> Optional[Dict[str, Any]]:
        """
        Compute the realized forward return between the decision date and up to
        HOLD_WINDOW trading days later using real closing prices.
        Returns None when the symbol/date cannot be evaluated yet (pending).
        """
        yf_symbol = self._resolve_symbol(symbol)
        if not yf_symbol:
            return None

        today = date.today()
        window_end = min(decision_dt + timedelta(days=HOLD_WINDOW * 2 + 7), today + timedelta(days=1))
        hist = self._get_history(yf_symbol, decision_dt - timedelta(days=5), window_end)
        if hist is None or hist.empty:
            return None

        closes = hist["Close"].dropna()
        if closes.empty:
            return None

        idx_dates = [ts.date() for ts in closes.index]

        # Entry = first trading day on/after the decision date
        entry_pos = None
        for i, d in enumerate(idx_dates):
            if d >= decision_dt:
                entry_pos = i
                break
        if entry_pos is None:
            return None

        # Need at least one forward trading day to evaluate
        if entry_pos >= len(closes) - 1:
            return None  # pending: no forward data yet

        exit_pos = min(entry_pos + HOLD_WINDOW, len(closes) - 1)
        entry_price = float(closes.iloc[entry_pos])
        exit_price = float(closes.iloc[exit_pos])
        if entry_price <= 0:
            return None

        return_pct = round((exit_price - entry_price) / entry_price * 100, 2)
        return {
            "yf_symbol": yf_symbol,
            "entry_date": idx_dates[entry_pos].isoformat(),
            "exit_date": idx_dates[exit_pos].isoformat(),
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "return_pct": return_pct,
            "forward_days": exit_pos - entry_pos,
        }

    # ── Main backtest ────────────────────────────────────────
    def run_backtest(self, force: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force and self._result_cache and (now - self._result_cache_ts) < CACHE_TTL:
            return self._result_cache

        records = history_storage.list_records(limit=100)
        if not records:
            return self._empty_stats()

        total_predictions = 0
        winning_trades = 0
        losing_trades = 0
        pending_count = 0
        unresolved_count = 0

        win_returns: List[float] = []
        loss_returns: List[float] = []
        strategy_returns: List[float] = []

        analyst_stats: Dict[str, Dict[str, int]] = {}
        decision_breakdown: Dict[str, Dict[str, int]] = {
            "BUY": {"total": 0, "win": 0},
            "SELL": {"total": 0, "win": 0},
            "HOLD": {"total": 0, "win": 0},
        }
        evaluations: List[Dict[str, Any]] = []

        for rec in records:
            decision_data = rec.get("decision") or {}
            pm = decision_data.get("pm") or {}
            pm_decision = (pm.get("decision") or "HOLD").upper()
            if pm_decision not in decision_breakdown:
                pm_decision = "HOLD"

            symbol = rec.get("symbol") or "Asset"
            decision_dt = _parse_decision_date(rec.get("timestamp") or "")
            if decision_dt is None:
                unresolved_count += 1
                continue

            # Skip placeholder symbols that carry no real ticker
            if symbol.strip().lower() in ("asset", "unknown", ""):
                unresolved_count += 1
                continue

            fwd = self._forward_return(symbol, decision_dt)
            if fwd is None:
                pending_count += 1
                continue

            return_pct = fwd["return_pct"]

            if pm_decision == "BUY":
                strat_return = return_pct
                is_win = return_pct > 0
            elif pm_decision == "SELL":
                strat_return = -return_pct
                is_win = return_pct < 0
            else:  # HOLD
                strat_return = 0.0
                is_win = abs(return_pct) < HOLD_BAND_PCT

            total_predictions += 1
            decision_breakdown[pm_decision]["total"] += 1
            if is_win:
                winning_trades += 1
                decision_breakdown[pm_decision]["win"] += 1
            else:
                losing_trades += 1

            if pm_decision in ("BUY", "SELL"):
                strategy_returns.append(strat_return)
                if strat_return > 0:
                    win_returns.append(strat_return)
                elif strat_return < 0:
                    loss_returns.append(strat_return)

            reports = rec.get("analysisReports") or {}
            if isinstance(reports, dict):
                for analyst_name, report in reports.items():
                    text = report if isinstance(report, str) else str(report)
                    stance = _stance_from_text(text)
                    if stance == 0:
                        continue
                    display = analyst_name.replace(" Analyst", "").strip() or analyst_name
                    st = analyst_stats.setdefault(display, {"total": 0, "correct": 0})
                    st["total"] += 1
                    correct = (stance > 0 and return_pct > 0) or (stance < 0 and return_pct < 0)
                    if correct:
                        st["correct"] += 1

            evaluations.append({
                "record_id": rec.get("id"),
                "symbol": symbol,
                "yf_symbol": fwd["yf_symbol"],
                "decision": pm_decision,
                "entry_date": fwd["entry_date"],
                "exit_date": fwd["exit_date"],
                "entry_price": fwd["entry_price"],
                "exit_price": fwd["exit_price"],
                "return_pct": return_pct,
                "is_win": is_win,
            })

        if total_predictions == 0:
            result = self._empty_stats()
            result["pending_count"] = pending_count
            result["unresolved_count"] = unresolved_count
            self._result_cache = result
            self._result_cache_ts = now
            return result

        win_rate = round(winning_trades / total_predictions * 100, 1)

        avg_win = sum(win_returns) / len(win_returns) if win_returns else 0.0
        avg_loss = sum(loss_returns) / len(loss_returns) if loss_returns else 0.0
        if avg_loss != 0:
            pl_ratio = round(avg_win / abs(avg_loss), 2)
            profit_loss_ratio = f"{pl_ratio} : 1"
        elif win_returns:
            profit_loss_ratio = "∞ : 1"
        else:
            profit_loss_ratio = "0 : 1"

        avg_return = round(sum(strategy_returns) / len(strategy_returns), 2) if strategy_returns else 0.0

        analyst_rankings = []
        for name, data in analyst_stats.items():
            acc = round(data["correct"] / data["total"] * 100, 1) if data["total"] > 0 else 0.0
            analyst_rankings.append({
                "analyst": name,
                "accuracy": acc,
                "total_evaluations": data["total"],
            })
        analyst_rankings.sort(key=lambda x: x["accuracy"], reverse=True)

        decision_stats = []
        for dtype, data in decision_breakdown.items():
            if data["total"] == 0:
                continue
            decision_stats.append({
                "decision": dtype,
                "total": data["total"],
                "win": data["win"],
                "win_rate": round(data["win"] / data["total"] * 100, 1),
            })

        result = {
            "total_predictions": total_predictions,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "pending_count": pending_count,
            "unresolved_count": unresolved_count,
            "win_rate": win_rate,
            "avg_return_pct": avg_return,
            "avg_win_pct": round(avg_win, 2),
            "avg_loss_pct": round(avg_loss, 2),
            "profit_loss_ratio": profit_loss_ratio,
            "analyst_rankings": analyst_rankings,
            "decision_stats": decision_stats,
            "evaluations": evaluations,
            "hold_window_days": HOLD_WINDOW,
            "data_source": "Yahoo Finance (real forward returns)",
        }

        self._result_cache = result
        self._result_cache_ts = now
        return result

    def _empty_stats(self) -> Dict[str, Any]:
        """Baseline structure when there is no evaluable history yet."""
        return {
            "total_predictions": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "pending_count": 0,
            "unresolved_count": 0,
            "win_rate": 0.0,
            "avg_return_pct": 0.0,
            "avg_win_pct": 0.0,
            "avg_loss_pct": 0.0,
            "profit_loss_ratio": "0 : 1",
            "analyst_rankings": [],
            "decision_stats": [],
            "evaluations": [],
            "hold_window_days": HOLD_WINDOW,
            "data_source": "Yahoo Finance (real forward returns)",
        }


accuracy_backtester = AccuracyBacktester()
