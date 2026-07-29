"""
Circuit Breaker — Fault-tolerance pattern for data providers.

After N consecutive failures, the breaker "opens" and skips the source
for a cooldown period.  This prevents wasted retries against APIs that
are temporarily unavailable (e.g. rate-limited, 503, DNS failure).

Adapted from ALSA market_data_service._CircuitBreaker.
"""

import time
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple circuit breaker: after N failures, skip source for cooldown_seconds."""

    def __init__(self, max_failures: int = 3, cooldown_seconds: int = 300):
        self._failures: Dict[str, int] = {}
        self._open_until: Dict[str, float] = {}
        self._max_failures = max_failures
        self._cooldown = cooldown_seconds

    def record_failure(self, source: str) -> None:
        """Record a failure for *source*.  Opens the breaker when the
        threshold is reached."""
        self._failures[source] = self._failures.get(source, 0) + 1
        if self._failures[source] >= self._max_failures:
            self._open_until[source] = time.time() + self._cooldown
            logger.warning(
                "[CircuitBreaker] %s OPEN for %ss after %s failures",
                source, self._cooldown, self._failures[source],
            )

    def record_success(self, source: str) -> None:
        """Reset the failure counter on a successful call."""
        self._failures[source] = 0
        self._open_until.pop(source, None)

    def is_open(self, source: str) -> bool:
        """Return True if *source*'s breaker is open (calls should be skipped)."""
        until = self._open_until.get(source, 0)
        if until and time.time() < until:
            return True
        # Cooldown expired — close the breaker automatically
        if until:
            self._open_until.pop(source, None)
            self._failures.pop(source, None)
        return False

    def status(self) -> Dict[str, dict]:
        """Return human-readable status of all tracked sources."""
        now = time.time()
        result = {}
        for source in set(list(self._failures.keys()) + list(self._open_until.keys())):
            until = self._open_until.get(source, 0)
            result[source] = {
                "failures": self._failures.get(source, 0),
                "is_open": bool(until and now < until),
                "remaining_cooldown_s": max(0, int(until - now)) if until else 0,
            }
        return result
