import pytest
from faos.services.prompting import registry

def test_jinja_macro_rendering():
    """Verify that Jinja base_prompt correctly renders macro data and enrichment text"""
    context_data = {
        "macro_data": {
            "USD/CNY": 7.25,
            "Source": "CFETS",
            "Date": "2024-01-01"
        },
        "fact_sheet": {
            "company_name": "TestCorp"
        },
        "quote": {
            "price": 150.0,
            "longName": "Test Corporation",
            "symbol": "TST"
        },
        "news": [
            {"title": "Great news", "sentiment": 0.8}
        ],
        "user_parameters": {
            "language": "zh",
            "is_final": True
        }
    }
    
    # fundamental_analyst is one of the templates we copied over
    prompt = registry.render_prompt(
        role="fundamental_analyst",
        context_data=context_data,
        language="zh",
        json_hint='"test": "value"'
    )
    
    # 1. Base Prompt tests
    assert "★ 实时汇率 USD/CNY: 7.25" in prompt
    assert "Test Corporation" in prompt
    assert "当前价格: 150.0" in prompt
    
    # 2. Enrichment text tests
    assert "ADDITIONAL CONTEXT DATA" in prompt
    assert "Great news" in prompt
    
    # 3. Role template tests
    assert "# 基本面分析师" in prompt or "基本面" in prompt
    
    # 4. JSON Hint tests
    assert '"test": "value"' in prompt
    assert "CRITICAL: You MUST output in the following JSON format ONLY:" in prompt

    # 5. Output structure tests (from base_prompt.jinja is_final_round=True)
    assert "<structured_data>" in prompt
