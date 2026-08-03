import pytest
from faos.services.reasoning.grounding_verifier import grounding_verifier

def test_grounding_verifier_text_annotation():
    """Verify that hallucinatory PE/Revenue are caught and annotated in text."""
    snapshot = {
        "quote": {
            "trailingPE": 15.5
        },
        "financials": {
            "totalRevenue": 2000000000.0  # 20亿
        }
    }
    
    # Text with a hallucinated PE and correct Revenue
    llm_output = "该公司的PE约为 25 倍，总营收达到 20 亿。"
    
    res = grounding_verifier.verify(llm_output, snapshot)
    
    # 2 claims should be found
    assert res.total_count == 2
    
    # The PE (25 vs 15.5) is wrong, Revenue (20亿 = 2B vs 2000000000) is correct
    assert res.verified_count == 1
    assert res.flagged_count == 1
    
    annotated = grounding_verifier.annotate_output(llm_output, res)
    assert "25 倍（⚠️实际15.50）" in annotated or "25（⚠️实际15.50）" in annotated
    assert "20 亿（⚠️" not in annotated  # Revenue should NOT be flagged

def test_grounding_verifier_dict_annotation():
    """Verify recursive dictionary annotation works."""
    snapshot = {
        "quote": {
            "trailingPE": 15.5
        }
    }
    
    data = {
        "summary": "公司的市盈率约为30倍。",
        "metrics": [
            {"name": "PE", "description": "由于P/E达到30，估值过高。"}
        ]
    }
    
    annotated_data = grounding_verifier.annotate_dict(data, snapshot)
    assert "30倍（⚠️实际15.50）" in annotated_data["summary"] or "30（⚠️实际15.50）" in annotated_data["summary"]
    assert "30（⚠️实际15.50）" in annotated_data["metrics"][0]["description"]
