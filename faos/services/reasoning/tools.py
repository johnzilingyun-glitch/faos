"""
LLM Tool Executor — exposes FAOS capabilities as OpenAI-compatible function tools.

The LLM agents can call these functions to fetch missing data (web search, etc.)
during multi-turn tool-calling loops.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from faos.services.provider.websearch_impl import WebSearchProvider
from faos.services.provider.models import ProviderRequest

logger = logging.getLogger(__name__)

# ── Tool Definitions (OpenAI format) ───────────────────────────────

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "搜索互联网获取实时金融信息。用于获取股票新闻、财报数据、估值指标、"
                "行业分析、宏观经济数据等。返回格式化的搜索结果摘要。"
                "Search the web for real-time financial information including stock news, "
                "earnings reports, valuation metrics, industry analysis, and macro data."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "搜索关键词。建议包含股票代码/名称和具体问题。"
                            "例如：'600584 长电科技 PE 估值 2025 财报' 或 '600519 贵州茅台 营收 净利润'"
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
]

# Gemini format (Google uses a different structure)
GEMINI_TOOL_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "function_declarations": [
            {
                "name": "web_search",
                "description": TOOL_DEFINITIONS[0]["function"]["description"],
                "parameters": TOOL_DEFINITIONS[0]["function"]["parameters"],
            }
        ]
    }
]


class ToolExecutor:
    """Executes tool calls dispatched by the LLM."""

    def __init__(self):
        self._websearch: Optional[WebSearchProvider] = None

    def _get_websearch(self) -> WebSearchProvider:
        if self._websearch is None:
            self._websearch = WebSearchProvider()
        return self._websearch

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool call and return the result as a JSON string."""
        if tool_name == "web_search":
            return await self._search(arguments.get("query", ""))
        return json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)

    async def _search(self, query: str) -> str:
        if not query:
            return json.dumps({"error": "Empty search query"}, ensure_ascii=False)
        try:
            provider = self._get_websearch()
            req = ProviderRequest(entity=query, parameters={"search_query": query})
            resp = await provider.fetch(req)
            if resp.status == "success" and resp.data:
                # Format results as a concise summary
                items = resp.data if isinstance(resp.data, list) else []
                if not items:
                    return json.dumps({"results": [], "note": "No results found"}, ensure_ascii=False)
                # Trim to top 8 results, extract key fields
                summary = []
                for item in items[:8]:
                    entry: Dict[str, Any] = {}
                    if isinstance(item, dict):
                        entry["title"] = item.get("title", "")
                        snippet = item.get("snippet") or item.get("content") or item.get("text") or ""
                        entry["snippet"] = snippet[:300] if snippet else ""
                        entry["url"] = item.get("url") or item.get("link") or ""
                        entry["source"] = item.get("source") or item.get("publisher") or ""
                    summary.append(entry)
                return json.dumps(
                    {"query": query, "total": len(items), "results": summary},
                    ensure_ascii=False,
                )
            return json.dumps({"error": resp.error or "Search failed"}, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Tool web_search failed: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# Singleton instance
tool_executor = ToolExecutor()
