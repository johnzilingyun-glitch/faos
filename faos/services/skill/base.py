from abc import ABC, abstractmethod
from faos.services.skill.models import SkillRequest, SkillResponse, SkillManifest

class BaseSkill(ABC):
    """
    Abstract base class for all Skills in FAOS.
    """
    
    @property
    @abstractmethod
    def manifest(self) -> SkillManifest:
        """Return the manifest describing this skill."""
        pass
        
    @abstractmethod
    async def execute(self, request: SkillRequest) -> SkillResponse:
        """
        Execute the skill logic given the request and context.
        """
        pass
