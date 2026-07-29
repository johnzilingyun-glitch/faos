import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, Optional, Tuple, Type

from pydantic import BaseModel

import time
from faos.core.context import ExecutionContext
from faos.services.reasoning.models import ReasoningRequest, ReasoningResponse
from faos.services.reasoning.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

class RateLimiter:
    """Token-bucket style rate limiter for API requests."""
    def __init__(self, min_interval: float = 1.5, max_concurrent: int = 3):
        self._min_interval = min_interval
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self):
        await self._semaphore.acquire()
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                await asyncio.sleep(wait_time)
            self._last_request_time = time.monotonic()

    def release(self):
        self._semaphore.release()

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.release()


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
        self.rate_limiter = RateLimiter(
            min_interval=float(os.environ.get("LLM_RATE_LIMIT_INTERVAL", "1.5")),
            max_concurrent=int(os.environ.get("LLM_RATE_LIMIT_CONCURRENCY", "3"))
        )

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
        Routes to the configured LLM provider with fallback logic.
        """
        logger.info(f"ReasoningService analyzing context for task {request.task_id}")

        initial_provider = self._resolve_provider(request)
        
        # Determine fallback chain based on initial provider
        fallback_chain = [initial_provider]
        if initial_provider == "deepseek":
            fallback_chain.extend(["openrouter", "gemini"])
        elif initial_provider == "openrouter":
            fallback_chain.extend(["deepseek", "gemini"])
        elif initial_provider == "gemini":
            fallback_chain.extend(["openrouter", "deepseek"])
            
        # Mock is always terminal
        if initial_provider == "mock":
            return await self._call_mock(request)

        for provider in fallback_chain:
            logger.info(f"Trying provider: {provider}")
            try:
                if provider == "gemini":
                    resp = await self._call_gemini(request)
                elif provider in ("deepseek", "openrouter"):
                    resp = await self._call_openai_compatible(request, provider)
                else:
                    resp = await self._call_mock(request)
                    
                # Basic quality gate
                if "[LLM Error]" not in resp.raw_response:
                    return resp
                else:
                    logger.warning(f"Provider {provider} returned error response, falling back...")
            except Exception as e:
                logger.warning(f"Provider {provider} raised exception: {e}, falling back...")

        return ReasoningResponse(
            task_id=request.task_id,
            insights={},
            confidence=0.0,
            raw_response="[LLM Error] All available LLM providers failed.",
            usage={}
        )

    def _resolve_provider(self, request: ReasoningRequest) -> str:
        """Resolve the effective provider for a request (per-request override wins)."""
        provider = self.provider
        if request.llm_config and request.llm_config.get("provider"):
            provider = str(request.llm_config["provider"]).lower()
        return provider

    async def analyze_structured(
        self,
        request: ReasoningRequest,
        response_model: Type[BaseModel],
        schema_hint: Optional[str] = None,
    ) -> Tuple[Optional[BaseModel], str]:
        """
        Structured reasoning: ask the LLM for JSON and parse it into
        ``response_model``. Returns ``(parsed_model_or_None, raw_text)``.

        Never raises: on parse failure it degrades to ``(None, raw_text)`` so the
        caller can fall back to free-text rendering.
        """
        provider = self._resolve_provider(request)

        # Mock mode: synthesize a valid structured stub (keeps tests offline).
        if provider == "mock":
            model = self._mock_structured(response_model, request.context_data)
            return model, model.model_dump_json()

        hint = schema_hint or json.dumps(response_model.model_json_schema(), ensure_ascii=False)
        json_instruction = (
            f"{request.prompt or ''}\n\n"
            "# OUTPUT FORMAT (STRICT)\n"
            "Respond with a SINGLE valid JSON object ONLY — no markdown fences, no prose "
            "before or after. Separate objective FACTS from subjective INFERENCES, and give "
            "every evidence/signal/inference a numeric confidence in [0,1]. Conform to this shape:\n"
            f"{hint}"
        )
        aug = request.model_copy(update={"prompt": json_instruction, "json_mode": True})
        resp = await self.analyze_context(aug)
        parsed = self._coerce(resp.raw_response, response_model)
        return parsed, resp.raw_response

    def _coerce(self, raw: str, response_model: Type[BaseModel]) -> Optional[BaseModel]:
        """Tolerantly parse JSON (possibly fenced, wrapped in prose, or with trailing text)."""
        if not raw:
            return None
        text = raw.strip()
        
        # 1. Strip Markdown code blocks
        fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
        if fence_match:
            try:
                return response_model.model_validate_json(fence_match.group(1))
            except Exception:
                pass

        # 2. Try direct parsing
        try:
            return response_model.model_validate_json(text)
        except Exception:
            pass

        # 3. Locate valid JSON substring from first '{' to last matching '}'
        first_brace = text.find("{")
        if first_brace != -1:
            idx = text.rfind("}")
            while idx > first_brace:
                candidate = text[first_brace : idx + 1]
                try:
                    return response_model.model_validate_json(candidate)
                except Exception:
                    idx = text.rfind("}", first_brace, idx - 1)

        return None

    def _mock_structured(self, response_model: Type[BaseModel], context_data: Dict[str, Any]) -> BaseModel:
        """Build a valid structured stub for offline/mock runs."""
        from faos.services.reasoning.schemas import (
            AnalystReport, Fact, Evidence, Signal, Inference,
        )

        quote = context_data.get("quote", {}) or {}
        news = context_data.get("news", []) or []
        symbol = (
            (context_data.get("user_parameters", {}) or {}).get("symbol")
            or quote.get("symbol", "UNKNOWN")
        )

        if response_model is AnalystReport:
            price = quote.get("price", 0.0)
            avg_sent = 0.0
            if isinstance(news, list) and news:
                avg_sent = sum(n.get("sentiment", 0.0) for n in news if isinstance(n, dict)) / len(news)
            return AnalystReport(
                facts=[Fact(metric="Price", value=str(price), source="quote")],
                evidence=(
                    [Evidence(id="E1", source="mock", headline=f"{symbol} mock evidence",
                              quantified_impact="n/a", confidence=0.5)]
                    if news else []
                ),
                signals=[Signal(name="Mock Sentiment", observation=f"avg sentiment {avg_sent:.2f}",
                                interpretation="neutral", confidence=0.6)],
                inferences=[Inference(statement="[Mock] structured analysis stub",
                                      based_on=["Price"], confidence=0.6)],
                summary=f"[Mock] Structured analysis for {symbol} at {price}.",
            )

        # Debate schemas (Phase 2). Lazy import avoids any import cycle.
        from faos.services.discussion.models import (
            BullCase, BearCase, DebateJudgment, Claim, Rebuttal, ClaimVerdict,
        )

        if response_model is BullCase:
            return BullCase(
                claims=[
                    Claim(id="C1", statement=f"[Mock] {symbol} valuation is attractive",
                          evidence_refs=["Price"], confidence=0.65),
                    Claim(id="C2", statement="[Mock] demand trend is favorable",
                          evidence_refs=["E1"], confidence=0.6),
                ],
                summary=f"[Mock] Bull case for {symbol}.",
            )

        if response_model is BearCase:
            bull_claims = context_data.get("bull_claims", []) or []
            first_id = bull_claims[0].get("id", "C1") if bull_claims else "C1"
            return BearCase(
                rebuttals=[Rebuttal(target_claim_id=first_id,
                                    counter="[Mock] valuation reflects peak-cycle earnings",
                                    strength=0.55)],
                extra_risks=[Claim(id="R1", statement="[Mock] commodity price pullback risk",
                                   confidence=0.5)],
                summary=f"[Mock] Bear case for {symbol}.",
            )

        if response_model is DebateJudgment:
            bull_claims = context_data.get("bull_claims", []) or []
            verdicts = [
                ClaimVerdict(claim_id=c.get("id", "C?"), winner="tie",
                             bull_confidence=0.55, bear_confidence=0.5, rationale="[Mock] balanced")
                for c in bull_claims
            ] or [ClaimVerdict(claim_id="C1", winner="tie", rationale="[Mock] balanced")]
            return DebateJudgment(
                verdicts=verdicts,
                overall_winner="tie",
                overall_confidence=0.55,
                investment_plan=f"[Mock] Neutral investment plan for {symbol}.",
            )

        from faos.services.discussion.models import RiskGuard
        if response_model is RiskGuard:
            return RiskGuard(
                stop_loss="[Mock] -8% from entry",
                position_sizing="[Mock] max 20% of portfolio",
                hedges=["[Mock] index put hedge"],
                risk_level="medium",
                risk_score=50,
                confidence=0.6,
                notes=f"[Mock] Stress test for {symbol} passed.",
            )

        from faos.services.decision.models import PMDecision, Scorecard
        if response_model is PMDecision:
            return PMDecision(
                action="HOLD",
                confidence=0.6,
                risk_score=50,
                rationale=f"[Mock] Balanced decision for {symbol}.",
                scorecard=Scorecard(
                    investment_score=55, risk_level="medium",
                    catalyst=3, valuation=3, macro=3, recommendation="Watch",
                ),
            )

        try:
            return response_model()
        except Exception:
            return response_model.model_construct()

    # ── Gemini Provider ─────────────────────────────────────────────

    def _extract_retry_delay(self, error_str: str, attempt: int, base_delay: float = 3.0) -> float:
        """Extract explicit retry delay (e.g. from 429/RESOURCE_EXHAUSTED messages) or fallback to exponential backoff."""
        delay = None
        m = re.search(r"retryDelay['\"]?:\s*['\"]?(\d+(?:\.\d+)?)s?", error_str, re.IGNORECASE)
        if not m:
            m = re.search(r"retry in (\d+(?:\.\d+)?)s", error_str, re.IGNORECASE)
        if m:
            try:
                delay = float(m.group(1)) + 1.0  # +1s safety buffer
            except ValueError:
                delay = None

        if delay is None or delay <= 0:
            delay = base_delay * (2 ** attempt)

        return min(delay, 65.0)

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
            context_data=request.context_data,
            is_rendered=request.is_rendered
        )

        # Build contents list
        contents = [user_message]
        
        from google.genai import types
        config_kwargs: Dict[str, Any] = {}
        # If the prompt is already fully rendered (Jinja), it's in user_message. Don't duplicate it in system_instruction.
        if request.prompt and not request.is_rendered:
            config_kwargs["system_instruction"] = request.prompt
        if request.json_mode:
            config_kwargs["response_mime_type"] = "application/json"
        config = types.GenerateContentConfig(**config_kwargs) if config_kwargs else None

        max_retries = int(os.environ.get("FAOS_LLM_MAX_RETRIES", "3"))
        base_delay = 3.0

        for attempt in range(max_retries + 1):
            try:
                async with self.rate_limiter:
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
                error_str = str(e)
                error_lower = error_str.lower()
                is_rate_limit = (
                    "429" in error_str
                    or "resource_exhausted" in error_lower
                    or "quota" in error_lower
                    or "rate limit" in error_lower
                    or "exceeded your current quota" in error_lower
                )
                is_daily_quota = (
                    "generate_content_free_tier_requests" in error_lower
                    or "requests_per_day" in error_lower
                    or "limit: 20" in error_lower
                )

                if is_daily_quota:
                    logger.error(f"Gemini API free tier daily quota limit reached: {e}")
                    return ReasoningResponse(
                        task_id=request.task_id,
                        insights={},
                        confidence=0.0,
                        raw_response=(
                            "[LLM Error 429] ⚠️ Google Gemini 免费层每日 20 次请求额度已用尽 (Free Tier Daily Limit Reached)。\n"
                            "👉 请点击页面右上角的 ⚙️【系统设置】，在 Provider 中切换为 DeepSeek、OpenRouter 或 Mock 模式，或配置您的专属 API Key。"
                        ),
                        usage={},
                    )

                if is_rate_limit and attempt < max_retries:
                    delay = self._extract_retry_delay(error_str, attempt, base_delay=base_delay)
                    logger.warning(
                        f"Gemini API rate limited (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {delay:.1f}s. Error: {e}"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Gemini API call failed: {e}")
                    error_msg = (
                        f"[LLM Error 429] 接口请求频率超限 (Rate Limited)。已自动重试 {max_retries} 次仍未成功，请稍后再试或在右上角【⚙️设置】中切换 API 模型。\n原始错误: {e}"
                        if is_rate_limit else f"[LLM Error] {str(e)}"
                    )
                    return ReasoningResponse(
                        task_id=request.task_id,
                        insights={},
                        confidence=0.0,
                        raw_response=error_msg,
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
                context_data=request.context_data,
                is_rendered=request.is_rendered
            )
            messages = []
            if request.prompt and not request.is_rendered:
                messages.append({"role": "system", "content": request.prompt})
                messages.append({"role": "user", "content": user_message})
            else:
                messages.append({"role": "user", "content": user_message})

            max_retries = int(os.environ.get("FAOS_LLM_MAX_RETRIES", "3"))
            
            for attempt in range(max_retries + 1):
                try:
                    create_kwargs: Dict[str, Any] = {"model": model, "messages": messages}
                    if request.json_mode:
                        create_kwargs["response_format"] = {"type": "json_object"}
                    async with self.rate_limiter:
                        response = await client.chat.completions.create(**create_kwargs)
                    break
                except Exception as e:
                    error_str = str(e)
                    error_lower = error_str.lower()
                    is_rate_limit = (
                        "429" in error_str
                        or "rate limit" in error_lower
                        or "quota" in error_lower
                        or "resource_exhausted" in error_lower
                    )
                    if is_rate_limit and attempt < max_retries:
                        delay = self._extract_retry_delay(error_str, attempt, base_delay=2.0)
                        logger.warning(
                            f"Rate limited by {provider.capitalize()} (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {delay:.1f}s. Error: {e}"
                        )
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

        # Follow-up Q&A mode: answer the user's question using report context
        if context_data.get("question"):
            question = context_data.get("question", "")
            report = context_data.get("analysis_report", "") or ""
            symbol = (context_data.get("user_parameters", {}) or {}).get("symbol", "该标的")
            report_snippet = report[:600]
            answer = (
                f"针对你的问题「{question}」，结合 {symbol} 当前研报要点：\n\n"
                f"{report_snippet}\n\n"
                f"[Mock 模式] 以上为基于现有研报的要点回应；配置真实 LLM (Gemini/DeepSeek/OpenRouter) 的 API Key 后，"
                f"将给出针对该问题的深度定制解答。当前回答已严格基于本次分析上下文，未触发新的分析流程。"
            )
            return ReasoningResponse(
                task_id=request.task_id,
                insights={},
                confidence=0.6,
                raw_response=answer,
                usage={"prompt_tokens": 120, "completion_tokens": 60, "total_tokens": 180},
            )

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
