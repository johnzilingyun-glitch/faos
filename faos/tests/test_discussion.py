import pytest
from unittest.mock import AsyncMock, MagicMock

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
            raw_response=f"Mocked response for prompt: {req.prompt}",
            usage={"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        )
        
    reasoning.analyze_context = AsyncMock(side_effect=mock_analyze)
    return reasoning

@pytest.mark.asyncio
async def test_discussion_service_spawns_agents(mock_reasoning):
    discussion = DiscussionService(mock_reasoning)
    
    req = DiscussionRequest(task_id="task-123", context_data={"market": {"price": 100}})
    resp = await discussion.discuss(req)
    
    assert resp.status == "success"
    
    # Check that it spawned 3 agents by default
    assert len(resp.opinions) == 3
    assert resp.opinions[0].name == "Fundamental Analyst"
    assert resp.opinions[1].name == "Technical Analyst"
    assert resp.opinions[2].name == "Risk Manager"
    
    # Check that ReasoningService was called 4 times (3 agents + 1 consensus)
    assert mock_reasoning.analyze_context.call_count == 4
    
    # Check consensus
    assert "3 expert opinions" in resp.consensus
    assert "positive" in resp.consensus  # Because avg_confidence is 0.8 > 0.7
