import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class PortfolioTracker:
    def __init__(self, initial_cash: float = 100000.0):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.holdings: Dict[str, float] = {}  # symbol -> shares
        self.history: List[Dict[str, any]] = [] # list of snapshots
        self.trade_log: List[Dict[str, any]] = []
        
    def execute_trade(self, date: str, symbol: str, action: str, price: float, confidence: float):
        """
        Execute a trade based on Agent's decision.
        For simplicity in this MVP:
        BUY: Invest 50% of available cash.
        SELL: Liquidate 100% of holdings.
        HOLD: Do nothing.
        """
        action = action.upper()
        if action == "BUY":
            investment_amount = self.cash * 0.5 * confidence # Scale by confidence
            if investment_amount > 0 and price > 0:
                shares = investment_amount / price
                self.cash -= investment_amount
                self.holdings[symbol] = self.holdings.get(symbol, 0) + shares
                
                self.trade_log.append({
                    "date": date,
                    "symbol": symbol,
                    "action": "BUY",
                    "price": price,
                    "shares": shares,
                    "amount": investment_amount
                })
                logger.info(f"[{date}] BUY {shares:.2f} shares of {symbol} at {price:.2f}")
                
        elif action == "SELL":
            shares = self.holdings.get(symbol, 0)
            if shares > 0 and price > 0:
                revenue = shares * price
                self.cash += revenue
                self.holdings[symbol] = 0
                
                self.trade_log.append({
                    "date": date,
                    "symbol": symbol,
                    "action": "SELL",
                    "price": price,
                    "shares": shares,
                    "amount": revenue
                })
                logger.info(f"[{date}] SELL {shares:.2f} shares of {symbol} at {price:.2f}")
                
    def snapshot(self, date: str, current_prices: Dict[str, float]):
        """Record the current portfolio value."""
        portfolio_value = self.cash
        for sym, shares in self.holdings.items():
            portfolio_value += shares * current_prices.get(sym, 0.0)
            
        self.history.append({
            "date": date,
            "cash": self.cash,
            "portfolio_value": portfolio_value
        })
        return portfolio_value
        
    def get_metrics(self):
        """Calculate basic backtest metrics."""
        if not self.history:
            return {}
            
        final_value = self.history[-1]["portfolio_value"]
        total_return = (final_value - self.initial_cash) / self.initial_cash
        
        # Max Drawdown
        peak = self.initial_cash
        max_dd = 0.0
        for snap in self.history:
            val = snap["portfolio_value"]
            if val > peak:
                peak = val
            dd = (peak - val) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                
        return {
            "initial_cash": self.initial_cash,
            "final_value": final_value,
            "total_return_pct": total_return * 100,
            "max_drawdown_pct": max_dd * 100,
            "trade_count": len(self.trade_log)
        }
