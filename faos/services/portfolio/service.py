import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("faos.portfolio")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "faos_portfolio.db")

class PortfolioService:
    def __init__(self, db_path: str = DB_PATH, initial_cash: float = 1000000.0):
        self.db_path = db_path
        self.initial_cash = initial_cash
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Create table for account summary
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS account (
                        id INTEGER PRIMARY KEY,
                        cash REAL NOT NULL
                    )
                """)
                # Create table for positions
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS positions (
                        symbol TEXT PRIMARY KEY,
                        shares REAL NOT NULL,
                        avg_price REAL NOT NULL,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Create table for trade history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        shares REAL NOT NULL,
                        price REAL NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reason TEXT
                    )
                """)
                
                # Initialize account if empty
                cursor.execute("SELECT count(*) as cnt FROM account")
                if cursor.fetchone()["cnt"] == 0:
                    cursor.execute("INSERT INTO account (id, cash) VALUES (1, ?)", (self.initial_cash,))
                conn.commit()
            logger.info(f"SQLite Portfolio DB initialized at: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite Portfolio DB: {e}")

    def get_account_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT cash FROM account WHERE id = 1")
            cash = cursor.fetchone()["cash"]
            
            cursor.execute("SELECT symbol, shares, avg_price FROM positions")
            positions = [dict(row) for row in cursor.fetchall()]
            
            return {
                "cash": cash,
                "positions": positions
            }

    def execute_trade(self, symbol: str, action: str, shares: float, price: float, reason: str = "") -> bool:
        """
        action: 'BUY' or 'SELL'
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT cash FROM account WHERE id = 1")
                cash = cursor.fetchone()["cash"]
                
                cursor.execute("SELECT shares, avg_price FROM positions WHERE symbol = ?", (symbol,))
                pos = cursor.fetchone()
                
                if action == "BUY":
                    cost = shares * price
                    if cash < cost:
                        logger.warning(f"Insufficient funds to buy {shares} of {symbol}. Cash: {cash}, Cost: {cost}")
                        return False
                        
                    new_cash = cash - cost
                    if pos:
                        old_shares = pos["shares"]
                        old_avg_price = pos["avg_price"]
                        new_shares = old_shares + shares
                        new_avg_price = ((old_shares * old_avg_price) + cost) / new_shares
                        cursor.execute("UPDATE positions SET shares = ?, avg_price = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?", (new_shares, new_avg_price, symbol))
                    else:
                        cursor.execute("INSERT INTO positions (symbol, shares, avg_price) VALUES (?, ?, ?)", (symbol, shares, price))
                        
                    cursor.execute("UPDATE account SET cash = ? WHERE id = 1", (new_cash,))
                    
                elif action == "SELL":
                    if not pos or pos["shares"] < shares:
                        logger.warning(f"Insufficient shares to sell {shares} of {symbol}.")
                        return False
                        
                    revenue = shares * price
                    new_cash = cash + revenue
                    new_shares = pos["shares"] - shares
                    
                    if new_shares <= 0.0001:  # Floating point safe zero
                        cursor.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
                    else:
                        cursor.execute("UPDATE positions SET shares = ?, updated_at = CURRENT_TIMESTAMP WHERE symbol = ?", (new_shares, symbol))
                        
                    cursor.execute("UPDATE account SET cash = ? WHERE id = 1", (new_cash,))
                    
                else:
                    return False
                    
                # Log trade
                cursor.execute("INSERT INTO trades (symbol, action, shares, price, reason) VALUES (?, ?, ?, ?, ?)", (symbol, action, shares, price, reason))
                
                conn.commit()
            logger.info(f"Successfully executed {action} {shares} shares of {symbol} at ${price}")
            return True
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return False

    def auto_invest(self, symbol: str, recommendation: str, confidence: float, current_price: float = 100.0, risk_score: float = 50.0):
        """
        Auto invest logic based on AI recommendation.
        If STRONG BUY or BUY with confidence >= 0.7, we buy a fixed percentage of current cash.
        """
        action = recommendation.upper()
        if action in ["STRONG BUY", "BUY"] and confidence >= 0.7:
            summary = self.get_account_summary()
            cash = summary["cash"]
            
            # Risk-adjusted position sizing: Lower risk score means we can invest more.
            # Max 20% of cash for a single position.
            invest_ratio = min(0.2, (100 - risk_score) / 100 * 0.3 * confidence)
            amount_to_invest = cash * invest_ratio
            
            if amount_to_invest > 0 and current_price > 0:
                shares = round(amount_to_invest / current_price, 2)
                if shares > 0:
                    reason = f"AI Signal: {action}, Confidence: {confidence:.2f}, Risk: {risk_score:.2f}"
                    self.execute_trade(symbol, "BUY", shares, current_price, reason)
        
        elif action in ["STRONG SELL", "SELL"]:
            summary = self.get_account_summary()
            pos = next((p for p in summary["positions"] if p["symbol"] == symbol), None)
            if pos:
                shares = pos["shares"]
                reason = f"AI Signal: {action}, Confidence: {confidence:.2f}"
                self.execute_trade(symbol, "SELL", shares, current_price, reason)
