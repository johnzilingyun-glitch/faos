"""
Central runtime configuration for FAOS.

All knobs are environment-driven so that deployments (and tests) can tune
behaviour without touching code. A single Settings instance is created per
TaskRuntime and shared with the API layer.
"""
import os
from dataclasses import dataclass, field
from typing import List


def _split_env(name: str, default: str) -> List[str]:
    raw = os.environ.get(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings for a FAOS instance."""

    # "mock" disables real network providers (deterministic, offline-friendly).
    env: str = field(default_factory=lambda: os.environ.get("FAOS_ENV", "dev").lower())

    # API layer
    cors_origins: List[str] = field(default_factory=lambda: _split_env(
        "FAOS_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ))
    # If set, every /api/* request must carry header X-API-Key with this value.
    # Empty means open access (local development default).
    api_key: str = field(default_factory=lambda: os.environ.get("FAOS_API_KEY", ""))

    # Execution engine
    node_timeout_seconds: float = field(default_factory=lambda: _float_env("FAOS_NODE_TIMEOUT", 300.0))
    node_max_retries: int = field(default_factory=lambda: _int_env("FAOS_NODE_RETRIES", 1))

    # Task/context retention (memory hygiene)
    task_context_ttl_seconds: float = field(default_factory=lambda: _float_env("FAOS_TASK_TTL", 600.0))
    max_active_tasks: int = field(default_factory=lambda: _int_env("FAOS_MAX_TASKS", 1000))

    @property
    def is_mock_env(self) -> bool:
        return self.env == "mock"
