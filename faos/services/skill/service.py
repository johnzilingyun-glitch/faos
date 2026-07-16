import logging
from typing import Dict, Optional

from faos.services.skill.base import BaseSkill
from faos.services.skill.models import SkillRequest, SkillResponse

logger = logging.getLogger(__name__)

class SkillService:
    """
    Skill Service acts as the business implementation center.
    It manages the registry of skills and routes Capability requests to the appropriate Skill.
    """
    def __init__(self):
        # Map capability names to Skill instances
        self.skills_by_capability: Dict[str, BaseSkill] = {}
        logger.info("SkillService initialized")

    def register_skill(self, skill: BaseSkill):
        manifest = skill.manifest
        self.skills_by_capability[manifest.capability] = skill
        logger.info(f"Registered skill {manifest.name} for capability {manifest.capability}")

    def get_skill(self, capability: str) -> Optional[BaseSkill]:
        return self.skills_by_capability.get(capability)

    async def execute_capability(self, capability: str, request: SkillRequest) -> SkillResponse:
        skill = self.get_skill(capability)
        if not skill:
            error_msg = f"No skill registered for capability: {capability}"
            logger.error(error_msg)
            return SkillResponse(status="failed", error=error_msg)

        logger.info(f"Executing capability {capability} via skill {skill.manifest.name}")
        try:
            response = await skill.execute(request)
            return response
        except Exception as e:
            logger.error(f"Skill execution failed for capability {capability}: {e}")
            return SkillResponse(status="failed", error=str(e))
