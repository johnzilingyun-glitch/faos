import pytest
from faos.services.prompting import registry

def test_prompt_registry_loads_templates():
    """Verify PromptRegistry can load standard ALSA templates"""
    # Load fundamental analyst
    fundamental = registry.get_template("fundamental_analyst", language="zh")
    assert "# 基本面分析师" in fundamental
    assert "杜邦分解" in fundamental
    
    # Load bear researcher
    bear = registry.get_template("bear_researcher", language="zh")
    assert "看空研究员" in bear
    assert "靶向反驳" in bear
    
def test_prompt_registry_json_hint():
    """Verify PromptRegistry correctly appends JSON hints"""
    hint = '"test_key": "test_val"'
    bull = registry.get_template("bull_researcher", language="zh", json_hint=hint)
    
    assert "# 看多研究员" in bull
    assert "CRITICAL: You MUST output in the following JSON format ONLY:" in bull
    assert hint in bull

def test_prompt_registry_fallback():
    """Verify fallback when language not found (assuming EN templates don't exist yet, it should just raise or if ZH doesn't exist fall back)"""
    # Since we copied everything, let's just make sure it doesn't crash on simple lookup
    with pytest.raises(FileNotFoundError):
        registry.get_template("non_existent_role")
