import os
from faos.services.security.service import SecurityGovernanceService

def test_security():
    sec_svc = SecurityGovernanceService()
    
    # 1. Test Secret Manager
    # It should retrieve from mock store
    mock_key = sec_svc.get_secret("MOCK_API_KEY")
    assert mock_key == "sk-mock-12345", f"Expected 'sk-mock-12345', got {mock_key}"
    
    # Temporarily set an env var
    os.environ["TEST_REAL_KEY"] = "real-key-from-env"
    env_key = sec_svc.get_secret("TEST_REAL_KEY")
    assert env_key == "real-key-from-env", f"Expected 'real-key-from-env', got {env_key}"
    
    print("SecretManager tests passed!")
    
    # 2. Test Policy Engine
    # By default, network is allowed
    assert sec_svc.check_network_access() == True
    
    # Provider access
    assert sec_svc.check_provider_access("yfinance_quote") == True
    
    # Test capping discussion rounds
    capped_rounds = sec_svc.validate_discussion_rounds(10)
    assert capped_rounds == 5, f"Expected 5, got {capped_rounds}"
    
    # Now let's modify the policy manually to test blocking
    sec_svc.policy_engine.policy.banned_providers = ["malicious_provider"]
    assert sec_svc.check_provider_access("malicious_provider") == False
    
    print("PolicyEngine tests passed!")
    print("\nAll Security & Governance tests passed successfully!")

if __name__ == "__main__":
    test_security()
