import pytest
from unittest.mock import AsyncMock

from faos.services.discussion.models import DiscussionRequest
from faos.services.discussion.service import DiscussionService
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningResponse

@pytest.fixture
def mock_reasoning():
    reasoning = ReasoningService()
    
    async def mock_analyze(req):
        return ReasoningResponse(
            task_id=req.task_id,
            insights={"symbol": "AAPL", "price": 150},
            confidence=0.8,
            raw_response=f"Mocked response for prompt: {req.prompt[:15]}...",
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        )
        
    reasoning.analyze_context = AsyncMock(side_effect=mock_analyze)

    async def mock_structured(req, response_model, schema_hint=None):
        # Return a minimal valid structured instance + its JSON.
        model = response_model()
        return model, model.model_dump_json()

    reasoning.analyze_structured = AsyncMock(side_effect=mock_structured)
    return reasoning

@pytest.mark.asyncio
async def test_discussion_service_multi_stage_debate(mock_reasoning):
    discussion = DiscussionService(mock_reasoning)
    
    req = DiscussionRequest(task_id="task-123", context_data={"market": {"price": 100}})
    resp = await discussion.discuss(req)
    
    assert resp.status == "success"
    
    # 9 opinions across stages (added Risk Manager + Chief Strategist)
    assert len(resp.opinions) == 9
    assert resp.opinions[0].name == "Bull Researcher"
    assert resp.opinions[1].name == "Bear Researcher"
    assert resp.opinions[2].name == "Research Manager"
    assert resp.opinions[3].name == "Aggressive Risk Debator"
    assert resp.opinions[4].name == "Conservative Risk Debator"
    assert resp.opinions[5].name == "Neutral Risk Debator"
    assert resp.opinions[6].name == "Risk Manager"
    assert resp.opinions[7].name == "Chief Risk Officer"
    assert resp.opinions[8].name == "Chief Strategist"
    
    # Debate roles (Bull/Bear/Manager/CRO) use STRUCTURED reasoning
    assert mock_reasoning.analyze_structured.call_count == 4
    # Risk debators (x4) + Chief Strategist use free-text reasoning
    assert mock_reasoning.analyze_context.call_count == 5
    
    # The debate opinions carry structured payloads (claims / rebuttals / judgment).
    assert resp.opinions[0].structured is not None
    assert resp.opinions[1].structured is not None
    assert resp.opinions[2].structured is not None
    
    # Check consensus contains both plans
    assert "--- Investment Plan ---" in resp.consensus
    assert "--- Risk Plan ---" in resp.consensus
