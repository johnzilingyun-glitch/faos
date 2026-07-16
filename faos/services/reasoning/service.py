import asyncio
import json
import logging
import os
from typing import Any, Dict

from faos.core.context import ExecutionContext
from faos.services.reasoning.models import ReasoningRequest, ReasoningResponse

logger = logging.getLogger(__name__)


class ReasoningService:
    """
    Reasoning Service acts as the AI Reasoning Center.
    Supports two modes controlled by env var FAOS_LLM_PROVIDER:
      - "mock" (default): Simulated responses for testing
      - "gemini": Real Google Gemini API calls
    """

    def __init__(self):
        self.provider = os.environ.get("FAOS_LLM_PROVIDER", "mock").lower()
        self.default_model = os.environ.get("FAOS_LLM_MODEL", "gemini-2.0-flash")
        self._client = None

        if self.provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                logger.warning(
                    "FAOS_LLM_PROVIDER=gemini but GEMINI_API_KEY is not set. "
                    "Falling back to mock mode."
                )
                self.provider = "mock"
            else:
                from google import genai
                self._client = genai.Client(api_key=api_key)
                logger.info(f"ReasoningService initialized with Gemini (model={self.default_model})")

        if self.provider == "mock":
            logger.info("ReasoningService initialized in MOCK mode")

    async def analyze_context(self, request: ReasoningRequest) -> ReasoningResponse:
        """
        Analyze the given context data and return reasoning insights.
        Routes to the configured LLM provider.
        """
        logger.info(f"ReasoningService analyzing context for task {request.task_id}")

        provider = self.provider
        if request.llm_config and "provider" in request.llm_config:
            provider = request.llm_config["provider"].lower()

        if provider == "gemini":
            return await self._call_gemini(request)
        elif provider in ("deepseek", "openrouter"):
            return await self._call_openai_compatible(request, provider)
        else:
            return await self._call_mock(request)

    # ── Gemini Provider ─────────────────────────────────────────────

    async def _call_gemini(self, request: ReasoningRequest) -> ReasoningResponse:
        """Call Google Gemini API with the agent prompt and context data."""
        model = request.model or self.default_model
        client = self._client
        
        if request.llm_config:
            if "model" in request.llm_config:
                model = request.llm_config["model"]
            if request.llm_config.get("api_key"):
                from google import genai
                client = genai.Client(api_key=request.llm_config["api_key"])
                
        if not client:
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response="[LLM Error] Missing API Key for Gemini Provider.",
                usage={},
            )

        # Build the user message from context data
        user_message = self._build_user_message(request.context_data)

        # Build contents list
        contents = []
        if request.prompt:
            # Use system instruction for persona
            contents.append(f"[System Instruction]\n{request.prompt}\n\n[User Data]\n{user_message}")
        else:
            contents.append(user_message)

        try:
            # Run the synchronous SDK call in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
            )

            raw_text = response.text or ""

            # Extract usage metadata
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                um = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(um, "prompt_token_count", 0) or 0,
                    "completion_tokens": getattr(um, "candidates_token_count", 0) or 0,
                    "total_tokens": getattr(um, "total_token_count", 0) or 0,
                }

            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response=raw_text,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            # Graceful degradation: return error text instead of crashing the pipeline
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response=f"[LLM Error] {str(e)}",
                usage={},
            )

    # ── OpenAI Compatible Provider ──────────────────────────────────

    async def _call_openai_compatible(self, request: ReasoningRequest, provider: str) -> ReasoningResponse:
        """Call DeepSeek or OpenRouter API using OpenAI SDK."""
        model = request.model or ("deepseek-v4-flash" if provider == "deepseek" else "openai/gpt-4o-mini")
        api_key = ""
        base_url = "https://api.deepseek.com" if provider == "deepseek" else "https://openrouter.ai/api/v1"

        if request.llm_config:
            if "model" in request.llm_config and request.llm_config["model"]:
                model = request.llm_config["model"]
            if request.llm_config.get("api_key"):
                api_key = request.llm_config["api_key"]

        if not api_key:
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response=f"[LLM Error] Missing API Key for {provider.capitalize()} Provider.",
                usage={},
            )

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            
            user_message = self._build_user_message(request.context_data)
            messages = []
            if request.prompt:
                messages.append({"role": "system", "content": request.prompt})
                messages.append({"role": "user", "content": user_message})
            else:
                messages.append({"role": "user", "content": user_message})

            response = await client.chat.completions.create(
                model=model,
                messages=messages,
            )

            raw_text = response.choices[0].message.content or ""
            usage = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response=raw_text,
                usage=usage,
            )

        except Exception as e:
            logger.error(f"{provider.capitalize()} API call failed: {e}")
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.0,
                raw_response=f"[LLM Error] {str(e)}",
                usage={},
            )

    # ── Mock Provider ───────────────────────────────────────────────

    async def _call_mock(self, request: ReasoningRequest) -> ReasoningResponse:
        """Simulated LLM for testing without API keys."""
        await asyncio.sleep(0.5)

        context_data = request.context_data
        quote = context_data.get("quote", {})
        news = context_data.get("news", [])

        avg_sentiment = 0.0
        if news:
            avg_sentiment = sum(n.get("sentiment", 0.0) for n in news) / len(news)

        insights = {
            "symbol": quote.get("symbol", "UNKNOWN"),
            "price": quote.get("price", 0.0),
            "sentiment": avg_sentiment,
            "target_price": quote.get("price", 0.0) * 1.1 if avg_sentiment > 0.5 else quote.get("price", 0.0),
        }

        raw_response = (
            f"Based on the analysis of {insights['symbol']} at price {insights['price']}, "
            f"and a market sentiment of {avg_sentiment:.2f}, "
            f"the target price is estimated at {insights['target_price']}."
        )

        if request.prompt:
            raw_response = f"[{request.prompt[:80]}...]\n{raw_response}"

        confidence = 0.85 if len(news) > 0 else 0.50

        return ReasoningResponse(
            task_id=request.task_id,
            insights=insights,
            confidence=confidence,
            raw_response=raw_response,
            usage={"prompt_tokens": 150, "completion_tokens": 50, "total_tokens": 200},
        )

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _build_user_message(context_data: Dict[str, Any]) -> str:
        """Convert context_data dict into a readable string for the LLM."""
        parts = []
        for key, value in context_data.items():
            if isinstance(value, (dict, list)):
                try:
                    serialized = json.dumps(value, indent=2, default=str, ensure_ascii=False)
                except Exception:
                    serialized = str(value)
                parts.append(f"## {key}\n```json\n{serialized}\n```")
            else:
                parts.append(f"## {key}\n{value}")
        return "\n\n".join(parts) if parts else "No context data provided."
