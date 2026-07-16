import asyncio
from faos.services.decision.models import DecisionPolicy, DecisionResult
from faos.services.decision.policy_engine import PolicyEngine

def test_guardrails():
    engine = PolicyEngine()
    
    # Test 1: Normal valid decision
    valid_dec = DecisionResult(
        action="BUY",
        score=85,
        confidence=0.9,
        risk=40,
        reason="Good fundamentals",
        evidence=["ROE is 20%"]
    )
    result1 = engine.evaluate_guardrails(valid_dec)
    assert result1.action == "BUY", "Valid decision should remain BUY"
    
    # Test 2: High risk decision
    risky_dec = DecisionResult(
        action="BUY",
        score=80,
        confidence=0.8,
        risk=90, # Above default 80
        reason="High reward potential",
        evidence=["Momentum is strong"]
    )
    result2 = engine.evaluate_guardrails(risky_dec)
    assert result2.action == "REJECT", "High risk should trigger REJECT guardrail"
    
    # Test 3: Low confidence decision
    low_conf_dec = DecisionResult(
        action="SELL",
        score=60,
        confidence=0.3, # Below default 0.5
        risk=30,
        reason="Not sure, but feels bearish",
        evidence=["Slight price drop"]
    )
    result3 = engine.evaluate_guardrails(low_conf_dec)
    assert result3.action == "REVIEW", "Low confidence should trigger REVIEW guardrail"
    
    # Test 4: Missing evidence
    no_ev_dec = DecisionResult(
        action="BUY",
        score=70,
        confidence=0.8,
        risk=20,
        reason="Just a hunch",
        evidence=[] # Missing evidence
    )
    result4 = engine.evaluate_guardrails(no_ev_dec)
    assert result4.action == "REJECT", "Missing evidence should trigger REJECT guardrail"
    
    print("All guardrail tests passed successfully!")

if __name__ == "__main__":
    test_guardrails()
