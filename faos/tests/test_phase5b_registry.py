import pytest
from faos.services.prompting import registry

def test_prompt_registry_loads_templates():
    """Verify PromptRegistry can load standard ALSA templates"""
    # Load fundamental analyst
    fundamental = registry.render_prompt("fundamental_analyst", context_data={}, language="zh")
    assert "# 基本面分析师" in fundamental
    assert "杜邦分解" in fundamental
    
    # Load bear researcher
    bear = registry.render_prompt("bear_researcher", context_data={}, language="zh")
    assert "看空研究员" in bear
    assert "靶向反驳" in bear
    
def test_prompt_registry_json_hint():
    """Verify PromptRegistry correctly appends JSON hints"""
    hint = '"test_key": "test_val"'
    bull = registry.render_prompt("bull_researcher", context_data={}, language="zh", json_hint=hint)
    
    assert "# 看多研究员" in bull
    assert "CRITICAL: You MUST output in the following JSON format ONLY:" in bull
    assert hint in bull

def test_prompt_registry_fallback():
    """Verify fallback when language not found"""
    with pytest.raises(FileNotFoundError):
        registry.render_prompt("non_existent_role", context_data={})
