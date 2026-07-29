import logging
from typing import Dict, Any
from dataclasses import dataclass
from faos.services.reasoning.schemas import AnalystReport

logger = logging.getLogger(__name__)

@dataclass
class GuardrailResult:
    passed: bool
    action: str  # "pass", "warn", "block"
    reason: str

def check_guardrails(report: AnalystReport) -> GuardrailResult:
    """
    Checks the structured report for logical inconsistencies or low confidence.
    Returns a GuardrailResult indicating whether the report should be blocked.
    """
    if not report.inferences:
        return GuardrailResult(passed=True, action="pass", reason="")

    # 1. Check Confidence
    avg_conf = sum(i.confidence for i in report.inferences) / len(report.inferences)
    if avg_conf < 0.4:
        return GuardrailResult(
            passed=False, 
            action="block", 
            reason=f"Average inference confidence too low ({avg_conf:.2f}). The model is hallucinating or lacking evidence."
        )

    # 2. Check Empty Evidence for strong statements
    if len(report.evidence) == 0 and len(report.facts) == 0:
        # If they made an inference but have zero facts/evidence
        return GuardrailResult(
            passed=False,
            action="block",
            reason="Inferences were made but no supporting facts or evidence were provided."
        )

    # 3. Contradiction Check (Heuristic)
    # If inference contains "买入"/"强烈推荐", but signals have very low confidence
    has_buy = any("买入" in i.statement or "看多" in i.statement for i in report.inferences)
    if has_buy and report.signals:
        avg_sig_conf = sum(s.confidence for s in report.signals) / len(report.signals)
        if avg_sig_conf < 0.3:
            return GuardrailResult(
                passed=False,
                action="block",
                reason=f"Inference suggests 'Buy' but signal confidence is extremely low ({avg_sig_conf:.2f})."
            )

    return GuardrailResult(passed=True, action="pass", reason="")
