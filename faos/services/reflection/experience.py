import os
import sqlite3
import json
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger("faos.experience")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "faos_history.db")


class ExperienceOptimizationService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_experience_memory (
                        id TEXT PRIMARY KEY,
                        category TEXT NOT NULL,
                        rule TEXT NOT NULL,
                        trigger_count INTEGER DEFAULT 1,
                        success_improvement TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
            logger.info("SQLite AI Experience Memory DB initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Experience DB: {e}")

    def _upsert(self, exp: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ai_experience_memory (id, category, rule, trigger_count, success_improvement, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    category = excluded.category,
                    rule = excluded.rule,
                    trigger_count = excluded.trigger_count,
                    success_improvement = excluded.success_improvement,
                    created_at = excluded.created_at
            """, (
                exp["id"], exp["category"], exp["rule"],
                exp.get("trigger_count", 1), exp.get("success_improvement", ""),
                exp.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
            ))
            conn.commit()

    def regenerate_from_backtest(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Derive concrete, data-grounded experience rules from a REAL backtest result
        and persist them (deterministic ids => upsert, no duplicates).
        """
        generated: List[Dict[str, Any]] = []
        total = stats.get("total_predictions", 0)
        if total <= 0:
            return self.list_experiences()

        now = time.strftime("%Y-%m-%d %H:%M:%S")
        win_rate = stats.get("win_rate", 0.0)
        pl_ratio = stats.get("profit_loss_ratio", "0 : 1")
        avg_win = stats.get("avg_win_pct", 0.0)
        avg_loss = stats.get("avg_loss_pct", 0.0)

        # Rule 1: overall accuracy assessment
        if win_rate >= 55:
            rule1 = f"近 {total} 次决策实测胜率 {win_rate}%，当前策略有效，维持现有多因子权重并逐步加仓验证。"
        elif win_rate >= 45:
            rule1 = f"近 {total} 次决策实测胜率 {win_rate}%，处于随机区间，建议提高置信度阈值、只执行高确定性信号。"
        else:
            rule1 = f"近 {total} 次决策实测胜率仅 {win_rate}%，需降低仓位并复核入场逻辑，警惕系统性偏差。"
        generated.append({
            "id": "auto_winrate",
            "category": "Backtest Insight",
            "rule": rule1,
            "trigger_count": total,
            "success_improvement": f"{win_rate}%",
            "created_at": now,
        })

        # Rule 2: profit/loss asymmetry
        if avg_loss != 0:
            rule2 = (
                f"实测盈亏比 {pl_ratio}（均盈 {avg_win}% / 均亏 {avg_loss}%）。"
                + ("盈亏结构健康，可让利润奔跑；" if avg_win >= abs(avg_loss) else "亏损幅度偏大，需收紧止损、缩短持有周期；")
                + "止损应参考 2×ATR 动态设置。"
            )
            generated.append({
                "id": "auto_pnl",
                "category": "Risk Management",
                "rule": rule2,
                "trigger_count": total,
                "success_improvement": pl_ratio.replace(" : 1", "x"),
                "created_at": now,
            })

        # Rule 3: best / worst decision type
        decision_stats = stats.get("decision_stats", [])
        if decision_stats:
            best = max(decision_stats, key=lambda x: x["win_rate"])
            worst = min(decision_stats, key=lambda x: x["win_rate"])
            if best["decision"] != worst["decision"]:
                rule3 = (
                    f"{best['decision']} 决策实测胜率 {best['win_rate']}% 最高，"
                    f"{worst['decision']} 仅 {worst['win_rate']}%。应放大 {best['decision']} 信号权重，"
                    f"对 {worst['decision']} 信号追加二次确认。"
                )
                generated.append({
                    "id": "auto_decision_bias",
                    "category": "Decision Calibration",
                    "rule": rule3,
                    "trigger_count": total,
                    "success_improvement": f"{best['win_rate']}%",
                    "created_at": now,
                })

        # Rule 4: strongest / weakest analyst
        rankings = stats.get("analyst_rankings", [])
        if rankings:
            top = rankings[0]
            bottom = rankings[-1]
            if top["analyst"] != bottom["analyst"]:
                rule4 = (
                    f"{top['analyst']} 分析师实测方向命中率 {top['accuracy']}% 领先，"
                    f"{bottom['analyst']} 仅 {bottom['accuracy']}%。共识阶段应上调 {top['analyst']} 观点权重。"
                )
                generated.append({
                    "id": "auto_analyst_weight",
                    "category": "Sentiment Calibration",
                    "rule": rule4,
                    "trigger_count": top.get("total_evaluations", total),
                    "success_improvement": f"{top['accuracy']}%",
                    "created_at": now,
                })

        try:
            for exp in generated:
                self._upsert(exp)
        except Exception as e:
            logger.error(f"Error persisting backtest-derived experiences: {e}")

        return self.list_experiences()

    def list_experiences(self) -> List[Dict[str, Any]]:
        """List all self-learned experience rules from SQLite."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, category, rule, trigger_count, success_improvement, created_at FROM ai_experience_memory ORDER BY rowid DESC")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error listing experiences: {e}")
            return []

    def add_experience(self, category: str, rule: str, success_improvement: str = "+10.0%") -> Dict[str, Any]:
        """Add a self-learned experience rule to memory."""
        exp_id = f"exp_{int(time.time())}"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO ai_experience_memory (id, category, rule, trigger_count, success_improvement)
                    VALUES (?, ?, ?, 1, ?)
                """, (exp_id, category, rule, success_improvement))
                conn.commit()
            logger.info(f"Added new AI experience rule {exp_id}: {rule}")
            return {"id": exp_id, "category": category, "rule": rule, "success_improvement": success_improvement}
        except Exception as e:
            logger.error(f"Error adding experience rule: {e}")
            return {}

experience_service = ExperienceOptimizationService()
