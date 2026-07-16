from faos.services.reasoning.prompt_builder import PromptBuilder
from faos.services.security.models import GlobalPolicy

def test_prompt_builder():
    policy = GlobalPolicy(max_tokens_per_task=5000, allow_network_access=False)
    builder = PromptBuilder(policy)
    
    # Test system prompt
    sys_prompt = builder.build_system_prompt(
        base_role="You are a senior financial analyst.",
        capabilities=["Analyze", "FetchNews"],
        knowledge="AAPL is a tech company."
    )
    
    assert "You are a senior financial analyst." in sys_prompt
    assert "FetchNews" in sys_prompt
    assert "AAPL is a tech company." in sys_prompt
    assert "5000" in sys_prompt
    assert "Network access is completely disabled" in sys_prompt
    
    # Test user prompt
    user_prompt = builder.build_user_prompt(
        intent="Analyze AAPL",
        context_data={"price": 150.0, "news": [{"title": "AAPL goes up"}]}
    )
    
    assert "Analyze AAPL" in user_prompt
    assert "150.0" in user_prompt
    assert "AAPL goes up" in user_prompt
    
    print("PromptBuilder tests passed successfully!")

if __name__ == "__main__":
    test_prompt_builder()
