"""OutputGuardrail — 输出侧校验拦截 (Phase 7).

校验大模型的最终决策 (PMDecision)，拦截低质、幻觉或矛盾的决策。
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from faos.services.decision.models import PMDecision

logger = logging.getLogger(__name__)


@dataclass
class GuardrailIssue:
    severity: str            # block / warn
    rule: str                # 规则名
    description: str


@dataclass
class GuardrailResult:
    passed: bool = True
    issues: list[GuardrailIssue] = field(default_factory=list)
    action: str = "pass"     # block / warn / pass
    # 拦截后的修正决策 (block 时覆盖原 decision)
    overridden_decision: Optional[PMDecision] = None

    def add(self, severity: str, rule: str, desc: str) -> None:
        self.issues.append(GuardrailIssue(severity, rule, desc))
        if severity == "block":
            self.action = "block"
            self.passed = False
        elif severity == "warn" and self.action != "block":
            self.action = "warn"


class OutputGuardrail:
    """输出侧 guardrail: 拦截低质 PMDecision."""

    # 阈值 (可配置)
    LOW_CONFIDENCE_THRESHOLD = 0.4
    HIGH_SCORE_THRESHOLD = 65
    LOW_SCORE_THRESHOLD = 40

    def check(self, decision: PMDecision) -> GuardrailResult:
        """校验 PMDecision 输出质量."""
        result = GuardrailResult()

        # 1. 低置信强制拦截
        if decision.confidence < self.LOW_CONFIDENCE_THRESHOLD and decision.action in ["BUY", "SELL"]:
            result.add("block", "low_confidence_act",
                       f"置信度过低({decision.confidence:.2f})却给出了明确的交易指令 {decision.action}")

        # 2. action-score 矛盾
        if decision.scorecard:
            score = decision.scorecard.investment_score
            if decision.action == "BUY" and score < self.LOW_SCORE_THRESHOLD:
                result.add("block", "action_score_contradiction",
                           f"action=BUY 但综合得分={score} < {self.LOW_SCORE_THRESHOLD}")
            if decision.action == "SELL" and score > self.HIGH_SCORE_THRESHOLD:
                result.add("block", "action_score_contradiction",
                           f"action=SELL 但综合得分={score} > {self.HIGH_SCORE_THRESHOLD}")

        # 3. 基础有效性
        if not decision.rationale or len(decision.rationale) < 10:
            result.add("block", "invalid_summary", "决策摘要(rationale)为空或过短，涉嫌敷衍")

        # block → 生成修正决策
        if result.action == "block":
            result.overridden_decision = self._override(decision)
            logger.warning("[Guardrail] 拦截决策: %s", [i.rule for i in result.issues if i.severity == "block"])

        return result

    @staticmethod
    def _override(decision: PMDecision) -> PMDecision:
        """拦截后修正: 强制 action=WATCH, confidence 降级."""
        decision.action = "WATCH"
        decision.confidence = min(decision.confidence, 0.3)
        decision.rationale = f"[GUARDRAIL 自动阻断并降级为 WATCH] {decision.rationale}"
        if decision.scorecard:
            decision.scorecard.recommendation = "WATCH"
        return decision

# 进程级默认实例
output_guardrail = OutputGuardrail()
