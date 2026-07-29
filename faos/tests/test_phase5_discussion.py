import pytest
from faos.services.discussion.models import DebateJudgment, Disagreement, ClaimVerdict

def test_debate_judgment_critic_parsing():
    """Verify that DebateJudgment correctly parses and renders Critic mechanisms."""
    judgment = DebateJudgment(
        consensus_points=["双方都认为该公司的营收在增长"],
        major_disagreements=[
            Disagreement(
                topic="盈利质量",
                bull_position="利润率稳定",
                bear_position="现金流与净利润背离，疑似做账",
                potential_impact="影响DCF估值的分子端"
            )
        ],
        data_conflicts=["多头引用财报净利润50亿，空头引用经营现金流-10亿"],
        verdicts=[
            ClaimVerdict(
                claim_id="C1",
                winner="bear",
                bull_confidence=0.5,
                bear_confidence=0.9,
                rationale="空头用OCF证伪了多头的利润论点"
            )
        ],
        overall_winner="bear",
        overall_confidence=0.8,
        investment_plan="不建议买入，因盈利质量存在重大争议"
    )
    
    rendered = judgment.render(lang="zh")
    
    assert "核心共识" in rendered
    assert "双方都认为该公司的营收在增长" in rendered
    
    assert "关键分歧点" in rendered
    assert "盈利质量" in rendered
    assert "多头: 利润率稳定" in rendered
    
    assert "数据冲突" in rendered
    assert "<mark>⚠️ 多头引用财报净利润50亿，空头引用经营现金流-10亿</mark>" in rendered
    
    assert "逐条裁决" in rendered
    assert "空头用OCF证伪了多头" in rendered
    assert "总体裁决" in rendered
    assert "空头" in rendered
    assert "80%" in rendered
    assert "投资共识计划" in rendered
