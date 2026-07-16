import pytest
import asyncio
from faos.core.context import ExecutionContext
from faos.services.skill.service import SkillService
from faos.services.skill.models import SkillRequest
from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill

@pytest.mark.asyncio
async def test_skill_service_registration_and_execution():
    service = SkillService()
    
    # Register skills
    service.register_skill(FetchDataSkill())
    service.register_skill(FetchNewsSkill())
    
    # Verify retrieval
    assert service.get_skill("FetchData") is not None
    assert service.get_skill("FetchNews") is not None
    assert service.get_skill("NonExistent") is None
    
    # Prepare context
    task_id = "test-task-001"
    context = ExecutionContext(task_id=task_id)
    
    # Execute FetchData
    req1 = SkillRequest(task_id=task_id, parameters={"symbol": "TSLA"}, context=context)
    resp1 = await service.execute_capability("FetchData", req1)
    
    assert resp1.status == "success"
    assert "quote" in context.provider_outputs
    assert context.provider_outputs["quote"]["symbol"] == "TSLA"
    
    # Execute non-existent
    resp2 = await service.execute_capability("NonExistent", req1)
    assert resp2.status == "failed"
    assert "No skill registered" in resp2.error
