import logging
from faos.services.security.models import GlobalPolicy

logger = logging.getLogger(__name__)

class GovernancePolicyEngine:
    """
    Central engine for all runtime, reasoning, and security policies.
    It evaluates whether a given action or configuration is permitted.
    """
    def __init__(self):
        # In a real system, this might be loaded from a database or config file
        self.policy = GlobalPolicy()
        logger.info("GovernancePolicyEngine initialized with default GlobalPolicy")

    def check_provider_access(self, provider_id: str) -> bool:
        if provider_id in self.policy.banned_providers:
            logger.warning(f"Access to provider '{provider_id}' is BANNED by policy.")
            return False
            
        if "*" in self.policy.allowed_providers or provider_id in self.policy.allowed_providers:
            return True
            
        logger.warning(f"Access to provider '{provider_id}' is NOT ALLOWED by policy.")
        return False
        
    def check_network_access(self) -> bool:
        if not self.policy.allow_network_access:
            logger.warning("Network access is blocked by policy.")
            return False
        return True

    def validate_discussion_rounds(self, requested_rounds: int) -> int:
        if requested_rounds > self.policy.max_discussion_rounds:
            logger.warning(f"Requested {requested_rounds} discussion rounds exceeds policy limit ({self.policy.max_discussion_rounds}). Capping.")
            return self.policy.max_discussion_rounds
        return requested_rounds
