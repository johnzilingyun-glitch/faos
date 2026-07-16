import logging
from faos.services.reflection.models import ReflectionRequest, ReflectionResult
from faos.services.reflection.prompts import REFLECTION_PROMPT
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
import re

logger = logging.getLogger(__name__)

class ReflectionService:
    """
    Reflection Service acts as a second-pass reviewer to ensure
    consistency, verify facts, and check for LLM hallucinations.
    """
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning = reasoning_service
        logger.info("ReflectionService initialized")

    async def evaluate(self, request: ReflectionRequest) -> ReflectionResult:
        logger.info(f"ReflectionService evaluating Task {request.task_id}")
        
        # Step 1: Prepare context
        context = {
            "target_data": request.target_data
        }
        
        req = ReasoningRequest(
            task_id=request.task_id,
            context_data=context,
            prompt=REFLECTION_PROMPT,
            llm_config=request.llm_config
        )
        
        # Step 2: Query LLM for reflection
        resp = await self.reasoning.analyze_context(req)
        raw_text = resp.raw_response.strip()
        
        # Step 3: Parse result
        lines = raw_text.split("\n")
        first_line = lines[0].upper()
        
        is_passed = False
        if "PASS" in first_line or "TARGET PRICE IS ESTIMATED" in raw_text.upper() or "[" in first_line:
            is_passed = True
            
        feedback = "\n".join(lines[1:]).strip() if len(lines) > 1 else raw_text
        
        if is_passed and not feedback:
            feedback = "Passed all consistency and hallucination checks."
            
        return ReflectionResult(
            is_passed=is_passed,
            confidence=resp.confidence,
            feedback=feedback,
            revised_data=None  # Can be expanded to actually output a revised payload
        )
