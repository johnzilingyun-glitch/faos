import logging
from typing import Optional

from faos.services.security.policy_engine import GovernancePolicyEngine
from faos.services.security.secret_manager import SecretManager
from faos.services.security.models import UserIdentity

logger = logging.getLogger(__name__)

class SecurityGovernanceService:
    """
    Security & Governance Service (Chapter 18).
    Provides a unified entrypoint for Policy enforcement, Secret Management, and RBAC.
    """
    def __init__(self):
        self.policy_engine = GovernancePolicyEngine()
        self.secret_manager = SecretManager()
        logger.info("SecurityGovernanceService initialized")

    def check_provider_access(self, provider_id: str, identity: Optional[UserIdentity] = None) -> bool:
        """
        Check if the given identity is allowed to access the specified provider.
        """
        # In MVP, we only check global policy, not individual RBAC.
        return self.policy_engine.check_provider_access(provider_id)

    def check_network_access(self, identity: Optional[UserIdentity] = None) -> bool:
        """
        Check if external network access is permitted.
        """
        return self.policy_engine.check_network_access()

    def get_secret(self, key: str, identity: Optional[UserIdentity] = None) -> Optional[str]:
        """
        Retrieve a secret, with an optional RBAC check.
        """
        # TODO: Add RBAC check to see if `identity` is allowed to read `key`
        return self.secret_manager.get_secret(key)

    def validate_discussion_rounds(self, requested_rounds: int) -> int:
        """
        Enforce max discussion round limits to prevent runaway LLM costs.
        """
        return self.policy_engine.validate_discussion_rounds(requested_rounds)
