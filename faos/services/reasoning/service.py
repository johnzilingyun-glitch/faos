import asyncio
import json
import logging
import os
from typing import Any, Dict

from faos.core.context import ExecutionContext
from faos.services.reasoning.models import ReasoningRequest, ReasoningResponse
from faos.services.reasoning.prompt_builder import PromptBuilder

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
        self.default_model = os.environ.get("FAOS_LLM_MODEL", "gemini-3.5-flash")
        self._client = None
        self.prompt_builder = PromptBuilder()

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
        user_message = self.prompt_builder.build_user_prompt(
            intent=request.prompt or "Analyze the provided context.",
            context_data=request.context_data
        )

        # Build contents list
        contents = [user_message]
        
        from google.genai import types
        config = None
        if request.prompt:
            config = types.GenerateContentConfig(
                system_instruction=request.prompt,
            )

        try:
            # Run the synchronous SDK call in a thread to avoid blocking the event loop
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
                config=config,
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
            import os
            if provider == "openrouter":
                api_key = os.environ.get("OPENROUTER_API_KEY", "")
            elif provider == "deepseek":
                api_key = os.environ.get("DEEPSEEK_API_KEY", "")

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
            
            user_message = self.prompt_builder.build_user_prompt(
                intent=request.prompt or "Analyze the provided context.",
                context_data=request.context_data
            )
            messages = []
            if request.prompt:
                messages.append({"role": "system", "content": request.prompt})
                messages.append({"role": "user", "content": user_message})
            else:
                messages.append({"role": "user", "content": user_message})

            max_retries = 3
            base_delay = 1.0
            
            for attempt in range(max_retries + 1):
                try:
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                    )
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    if ("429" in error_str or "rate limit" in error_str) and attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Rate limited by {provider.capitalize()}. Retrying in {delay} seconds (Attempt {attempt+1}/{max_retries}). Error: {e}")
                        await asyncio.sleep(delay)
                    else:
                        raise e

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
            if "workflow_id" in request.prompt and "parameters" in request.prompt:
                # Mock a planner JSON response
                intent = context_data.get("intent", "") or context_data.get("conversation_history", "")
                words = intent.split()
                symbol = next((w for w in words if (w.isupper() and len(w) <= 5) or ".HK" in w.upper() or ".SS" in w.upper() or ".SZ" in w.upper()), "AAPL")
                
                intent_lower = intent.lower()
                if "腾讯" in intent or "0700" in intent: symbol = "0700.HK"
                elif "宝丰" in intent or "600989" in intent: symbol = "600989.SS"
                elif "茅台" in intent or "600519" in intent: symbol = "600519.SS"
                elif "特斯拉" in intent or "tsla" in intent_lower: symbol = "TSLA"
                elif "苹果" in intent or "aapl" in intent_lower: symbol = "AAPL"
                elif "微软" in intent or "msft" in intent_lower: symbol = "MSFT"
                
                raw_response = json.dumps({
                    "status": "ready",
                    "message": f"Starting analysis for {symbol}",
                    "workflow_id": "AnalyzeStockWorkflow",
                    "parameters": {"symbol": symbol},
                    "reasoning": f"Mock planner identified symbol {symbol} from intent."
                })
            else:
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
    # _build_user_message is now handled by PromptBuilder
