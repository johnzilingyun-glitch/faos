import pytest
from faos.services.security.grounding import verify_and_annotate
from faos.services.security.guardrail import check_guardrails, GuardrailResult
from faos.services.reasoning.schemas import AnalystReport

def test_grounding_verifier():
    """Verify that hallucinated numbers are properly tagged."""
    facts = {
        "pe": 18.2,
        "revenue": 1000000000, # 10亿
        "roe": 0.15 # 15%
    }
    
    # Text with correct numbers (within 5% tolerance)
    good_text = "该公司的PE约18.5倍，总营收达到10亿，ROE为15%。"
    good_annotated = verify_and_annotate(good_text, facts)
    assert "<mark>" not in good_annotated
    
    # Text with hallucinated numbers
    bad_text = "我编造的PE是100倍，总营收达到500亿，ROE为30%。"
    bad_annotated = verify_and_annotate(bad_text, facts)
    
    assert "<mark>⚠️ 数据查证不符，底层真实 PE 为 18.20</mark>" in bad_annotated
    assert "<mark>⚠️ 数据查证不符，底层真实 REVENUE 为 10.00亿</mark>" in bad_annotated
    assert "<mark>⚠️ 数据查证不符，底层真实 ROE 为 15.00%</mark>" in bad_annotated

from faos.services.reasoning.schemas import AnalystReport, Inference, Signal

def test_guardrail_block_confidence():
    """Verify guardrail blocks low confidence reports."""
    report = AnalystReport(
        summary="我不确定",
        inferences=[Inference(statement="买入", confidence=0.3)], # < 0.4 triggers block
        facts=[], evidence=[], signals=[]
    )
    res = check_guardrails(report)
    assert res.passed is False
    assert res.action == "block"
    assert "confidence too low" in res.reason.lower()

from faos.services.reasoning.schemas import AnalystReport, Inference, Signal, Fact

def test_guardrail_block_contradiction():
    """Verify guardrail blocks contradictory scores and actions."""
    report = AnalystReport(
        summary="赶紧买",
        inferences=[Inference(statement="强烈建议买入", confidence=0.8)],
        signals=[Signal(name="RSI", observation="超买", confidence=0.2)], # Action is buy, but signal conf is < 0.3
        facts=[Fact(metric="PE", value="10")], evidence=[]
    )
    res = check_guardrails(report)
    assert res.passed is False
    assert res.action == "block"
    assert "buy" in res.reason.lower() or "contradiction" in res.reason.lower() or "extremely low" in res.reason.lower()

def test_guardrail_block_empty_evidence():
    """Verify guardrail blocks decisive actions with no evidence."""
    report = AnalystReport(
        summary="建议卖出",
        inferences=[Inference(statement="建议卖出", confidence=0.8)],
        facts=[], evidence=[], signals=[] # Empty evidence!
    )
    res = check_guardrails(report)
    assert res.passed is False
    assert res.action == "block"
    assert "no supporting facts or evidence" in res.reason.lower()
