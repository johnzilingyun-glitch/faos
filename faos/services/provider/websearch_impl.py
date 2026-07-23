import os
import json
import asyncio
import logging
import hashlib
from typing import Dict, Any, List, Optional
import httpx
from pydantic import Field

from faos.services.provider.base import BaseProvider
from faos.services.provider.models import ProviderRequest, ProviderResponse, ProviderManifest

logger = logging.getLogger(__name__)

class WebSearchProvider(BaseProvider):
    # Class-level memory cache fallback (lives as long as the process)
    _memory_cache: Dict[str, str] = {}
    
    def __init__(self):
        # We initialize redis client lazily or handle import cleanly
        self.redis_client = None
        # Hardcoding the API key provided by the user, but still allowing env override
        self.tavily_api_key = os.environ.get("TAVILY_API_KEY", "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")
        self.serper_api_key = os.environ.get("SERPER_API_KEY", "ce54c5b01ef640bc086f96b4c511aef7fcb56c66")
        self.jina_api_key = os.environ.get("JINA_API_KEY", "jina_536c44d451074d0f82a5dcd1967f01banpUgiyNUWAaFEoEaNoIJpxj_OJw_")
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        
    async def _init_redis(self):
        if self.redis_client is None:
            try:
                import fakeredis.aioredis as redis
                self.redis_client = redis.FakeRedis()
                # Test connection briefly
                await self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Could not init fakeredis: {e}. Falling back to in-memory cache.")
                self.redis_client = False # False means we tried and failed

    @property
    def manifest(self) -> ProviderManifest:
        return ProviderManifest(
            id="web_search",
            name="Web Search Provider (Tavily/Serper + Cache)",
            category="news",
            capabilities=["web_search", "news_search"],
            priority=200  # Higher priority to override mock/yfinance if applicable
        )

    async def fetch(self, request: ProviderRequest) -> ProviderResponse:
        query = request.entity
        
        # 1. Check Cache
        await self._init_redis()
        cache_key = f"faos:websearch:{hashlib.md5(query.encode()).hexdigest()}"
        
        cached = None
        if self.redis_client:
            try:
                cached = await self.redis_client.get(cache_key)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        else:
            cached = self._memory_cache.get(cache_key)
            
        if cached:
            logger.info(f"Cache hit for query: {query}")
            return ProviderResponse(status="success", data=json.loads(cached))

        # 2. Try providers in order
        results = None
        errors = []
        
        if self.tavily_api_key:
            try:
                logger.info("Searching via Tavily...")
                results = await self._search_tavily(query)
            except Exception as e:
                logger.error(f"Tavily search failed (possibly out of quota): {e}")
                errors.append(f"Tavily: {e}")
                
        if results is None and self.serper_api_key:
            try:
                logger.info("Falling back to Serper...")
                results = await self._search_serper(query)
            except Exception as e:
                logger.error(f"Serper search failed: {e}")
                errors.append(f"Serper: {e}")
                
        if results is None and getattr(self, 'jina_api_key', None):
            try:
                logger.info("Falling back to Jina...")
                results = await self._search_jina(query)
            except Exception as e:
                logger.error(f"Jina search failed: {e}")
                errors.append(f"Jina: {e}")

        if results is None:
            return ProviderResponse(status="error", error=f"All search providers failed. Errors: {errors}")

        if results is not None:
            # 4. Save to Cache
            if self.redis_client:
                try:
                    await self.redis_client.setex(cache_key, 7200, json.dumps(results))
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
            else:
                self._memory_cache[cache_key] = json.dumps(results)
            
            return ProviderResponse(status="success", data=results)
        
        return ProviderResponse(status="error", error="Unknown error producing results")

    async def _search_tavily(self, query: str) -> List[Dict[str, str]]:
        url = "https://api.tavily.com/search"
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "api_key": self.tavily_api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": False,
                "max_results": 5
            }
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("content", ""),
                    "source": "Tavily"
                })
            return results

    async def _search_serper(self, query: str) -> List[Dict[str, str]]:
        url = "https://google.serper.dev/search"
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "q": query
            }
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            # Check organic results
            for item in data.get("organic", [])[:5]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Serper (Google)"
                })
            return results

    async def _search_jina(self, query: str) -> List[Dict[str, str]]:
        url = f"https://s.jina.ai/{query}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {
                'Authorization': f'Bearer {self.jina_api_key}',
                'Accept': 'application/json'
            }
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            
            results = []
            for item in data.get("data", [])[:5]:
                snippet = item.get("description", "")
                if not snippet:
                    content = item.get("content", "")
                    snippet = content[:200] if content else ""
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": snippet,
                    "source": "Jina Search"
                })
            return results
