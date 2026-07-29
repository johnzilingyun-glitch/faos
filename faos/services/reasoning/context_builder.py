"""
Context Builder — Aggregates and formats data for the LLM using TokenGuard.

This module provides a standard way to build the context dictionary expected
by the ReasoningService and PromptBuilder. It leverages the TokenGuard to ensure
the data does not blow up the context window.
"""

import json
from typing import Dict, Any, List

from faos.services.reasoning.token_guard import token_guard, compact_json

class ContextBuilder:
    """
    Builds the context_data dictionary for the LLM, applying limits and
    compression where necessary.
    """

    @staticmethod
    def build_quote_context(quote_data: Dict[str, Any]) -> str:
        """Format and compress quote data."""
        if not quote_data:
            return "{}"
        
        # Enforce TokenGuard (treat it as a tool output)
        raw_json = compact_json(quote_data)
        safe_json = token_guard.enforce("get_stock_quote", raw_json)
        return safe_json

    @staticmethod
    def build_indicators_context(indicators_data: Dict[str, Any]) -> str:
        """Format and compress technical indicators."""
        if not indicators_data:
            return "{}"
        
        raw_json = compact_json(indicators_data)
        safe_json = token_guard.enforce("get_technical_indicators", raw_json)
        return safe_json

    @staticmethod
    def build_news_context(news_items: List[Dict[str, Any]]) -> str:
        """Format and compress news items."""
        if not news_items:
            return "[]"
        
        # Convert list of dicts to string
        raw_json = compact_json(news_items)
        safe_json = token_guard.enforce("get_news", raw_json)
        return safe_json
    
    @staticmethod
    def build_financial_context(financial_data: Dict[str, Any]) -> str:
        """Format and compress financial data."""
        if not financial_data:
            return "{}"
        
        raw_json = compact_json(financial_data)
        safe_json = token_guard.enforce("financial_data", raw_json)
        return safe_json

    @classmethod
    def assemble_context(
        cls,
        symbol: str,
        quote: Dict[str, Any] = None,
        indicators: Dict[str, Any] = None,
        news: List[Dict[str, Any]] = None,
        financials: Dict[str, Any] = None,
        extra: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Assemble the final context_data dict to be passed to ReasoningService.
        Reset the TokenGuard round budget before building.
        """
        token_guard.reset_round()

        context_data = {
            "user_parameters": {"symbol": symbol},
            "quote_str": cls.build_quote_context(quote or {}),
            "indicators_str": cls.build_indicators_context(indicators or {}),
            "news_str": cls.build_news_context(news or []),
            "financials_str": cls.build_financial_context(financials or {})
        }

        if extra:
            context_data.update(extra)

        return context_data
