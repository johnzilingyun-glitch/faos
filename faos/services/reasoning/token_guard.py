"""
Token Guard — Defensive middleware to prevent tool outputs from returning excessive data to LLM.

Architecture:
  1. Per-tool hard limits (MAX chars/rows)
  2. Global per-round token budget enforcement
  3. Structured output compression
  4. Emergency circuit breaker
"""

import json
from dataclasses import dataclass, field
from typing import Optional, Literal

GuardLevel = Literal["none", "low", "medium", "high"]
VALID_LEVELS = ("none", "low", "medium", "high")

@dataclass
class ToolLimit:
    max_chars: int = 4000
    max_rows: int = 10
    max_field_chars: int = 200
    max_fields_per_row: int = 8

@dataclass
class GuardConfig:
    round_budget_chars: int = 25000
    default_limit: ToolLimit = field(default_factory=ToolLimit)
    tool_limits: dict = field(default_factory=dict)
    emergency_max_chars: int = 8000
    enabled: bool = True

def _build_tool_limits(multiplier: float) -> dict:
    base = {
        "get_stock_quote": ToolLimit(max_chars=2000, max_rows=1, max_field_chars=100),
        "get_technical_indicators": ToolLimit(max_chars=3000, max_rows=10, max_field_chars=200),
        "get_news": ToolLimit(max_chars=5000, max_rows=5, max_field_chars=800),
        "financial_data": ToolLimit(max_chars=5000, max_rows=6, max_field_chars=500),
    }
    if multiplier == 1.0:
        return base
    scaled = {}
    for name, lim in base.items():
        scaled[name] = ToolLimit(
            max_chars=int(lim.max_chars * multiplier),
            max_rows=min(int(lim.max_rows * multiplier), 50),
            max_field_chars=int(lim.max_field_chars * multiplier),
            max_fields_per_row=int(lim.max_fields_per_row * multiplier),
        )
    return scaled

LEVEL_CONFIGS: dict[str, GuardConfig] = {
    "none": GuardConfig(
        round_budget_chars=999_999_999,
        default_limit=ToolLimit(max_chars=999_999, max_rows=9999, max_field_chars=999_999),
        tool_limits={},
        emergency_max_chars=999_999_999,
        enabled=False,
    ),
    "low": GuardConfig(
        round_budget_chars=75000,
        default_limit=ToolLimit(max_chars=12000, max_rows=30, max_field_chars=600),
        tool_limits=_build_tool_limits(3.0),
        emergency_max_chars=24000,
        enabled=True,
    ),
    "medium": GuardConfig(
        round_budget_chars=40000,
        default_limit=ToolLimit(max_chars=6000, max_rows=15, max_field_chars=400),
        tool_limits=_build_tool_limits(1.5),
        emergency_max_chars=12000,
        enabled=True,
    ),
    "high": GuardConfig(
        round_budget_chars=25000,
        default_limit=ToolLimit(max_chars=4000, max_rows=10, max_field_chars=200),
        tool_limits=_build_tool_limits(1.0),
        emergency_max_chars=8000,
        enabled=True,
    ),
}

DEFAULT_LEVEL: GuardLevel = "high"

class TokenGuard:
    def __init__(self, config: Optional[GuardConfig] = None, level: GuardLevel = DEFAULT_LEVEL):
        self._level = level
        self.config = config or LEVEL_CONFIGS[level]
        self._round_chars_used = 0
        self._round_tool_count = 0

    @property
    def level(self) -> GuardLevel:
        return self._level

    def set_level(self, level: str):
        level = level.lower().strip()
        if level not in VALID_LEVELS:
            return
        if level == self._level:
            return
        self._level = level
        self.config = LEVEL_CONFIGS[level]
        self.reset_round()

    def reset_round(self):
        self._round_chars_used = 0
        self._round_tool_count = 0

    @property
    def round_budget_remaining(self) -> int:
        return max(0, self.config.round_budget_chars - self._round_chars_used)

    def get_limit(self, tool_name: str) -> ToolLimit:
        return self.config.tool_limits.get(tool_name, self.config.default_limit)

    def enforce(self, tool_name: str, raw_output: str) -> str:
        if not raw_output or not self.config.enabled:
            return raw_output

        limit = self.get_limit(tool_name)
        original_len = len(raw_output)

        effective_max = min(limit.max_chars, self.config.emergency_max_chars)
        budget_max = max(1000, self.round_budget_remaining)
        effective_max = min(effective_max, budget_max)

        if len(raw_output) > effective_max:
            truncated = raw_output[:effective_max]
            # Try to break at a newline safely
            last_newline = truncated.rfind('\n', effective_max - 200)
            if last_newline > effective_max * 0.8:
                truncated = truncated[:last_newline]
            output = truncated + f"\n\n... [truncated: {original_len} → {len(truncated)} chars, tool budget limit]"
        else:
            output = raw_output

        self._round_chars_used += len(output)
        self._round_tool_count += 1
        return output

token_guard = TokenGuard()

def compact_json(data, ensure_ascii=False) -> str:
    return json.dumps(data, ensure_ascii=ensure_ascii, separators=(',', ':'))

def slim_dict(d: dict, whitelist: list, max_field_chars: int = 200) -> dict:
    result = {}
    for key in whitelist:
        if key in d:
            val = d[key]
            if isinstance(val, str) and len(val) > max_field_chars:
                val = val[:max_field_chars] + "..."
            result[key] = val
    return result

def slim_list(items: list, max_items: int, whitelist: list = None, max_field_chars: int = 200) -> list:
    sliced = items[:max_items]
    if whitelist:
        return [slim_dict(item, whitelist, max_field_chars) for item in sliced if isinstance(item, dict)]
    return sliced
