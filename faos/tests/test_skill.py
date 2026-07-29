import pytest
import asyncio
from faos.core.context import ExecutionContext
from faos.services.skill.service import SkillService
from faos.services.skill.models import SkillRequest
from faos.services.skill.impl import FetchDataSkill, FetchNewsSkill
from faos.services.provider.service import ProviderService
from faos.services.provider.impl import MockQuoteProvider, MockNewsProvider

@pytest.mark.asyncio
async def test_skill_service_registration_and_execution():
    service = SkillService()
    
    provider_service = ProviderService()
    provider_service.register_provider(MockQuoteProvider())
    provider_service.register_provider(MockNewsProvider())
    
    from faos.services.data_route.service import DataRouteService
    data_route = DataRouteService(provider_service)

    # Register skills
    service.register_skill(FetchDataSkill(data_route=data_route))
    service.register_skill(FetchNewsSkill(data_route=data_route))
    
    # Verify retrieval
    assert service.get_skill("cap.fetch_data") is not None
    assert service.get_skill("cap.fetch_news") is not None
    assert service.get_skill("NonExistent") is None
    
    # Prepare context
    task_id = "test-task-001"
    context = ExecutionContext(task_id=task_id)
    
    # Execute FetchData
    req1 = SkillRequest(task_id=task_id, parameters={"symbol": "TSLA"}, context=context)
    resp1 = await service.execute_capability("cap.fetch_data", req1)
    
    assert resp1.status == "success"
    assert "quote" in context.provider_outputs
    assert context.provider_outputs["quote"]["symbol"] == "TSLA"
    
    # Execute non-existent
    resp2 = await service.execute_capability("NonExistent", req1)
    assert resp2.status == "failed"
    assert "No skill registered" in resp2.error
