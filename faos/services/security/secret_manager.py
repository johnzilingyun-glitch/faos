import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecretManager:
    """
    Manages sensitive credentials like API Keys.
    Prevents hardcoding secrets in providers or skills.
    In MVP, it reads from environment variables or a local dict.
    In production, this interfaces with HashiCorp Vault or AWS Secrets Manager.
    """
    def __init__(self):
        # A mock store for testing if env vars are not set
        self._mock_store = {
            "MOCK_API_KEY": "sk-mock-12345",
            "YFINANCE_TOKEN": "mock-yf-token"
        }
        logger.info("SecretManager initialized")

    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieve a secret by key.
        Order of precedence: Environment Variable -> Mock Store.
        """
        # 1. Try Environment Variable (Production standard for MVP)
        val = os.environ.get(key)
        if val:
            return val
            
        # 2. Try Mock Store (For testing / fallback)
        val = self._mock_store.get(key)
        if val:
            logger.debug(f"Retrieved {key} from mock secret store")
            return val
            
        logger.warning(f"Secret for {key} not found!")
        return None
        
    def set_secret(self, key: str, value: str):
        """
        Store a secret in the mock store (runtime only, not persistent).
        """
        self._mock_store[key] = value
        logger.info(f"Secret {key} temporarily stored in SecretManager")
