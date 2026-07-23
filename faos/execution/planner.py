import logging
import json
from typing import Optional, List, Dict, Any
from faos.core.models import Event, ExecutionPlan, PlanNode
from faos.core.event_bus import EventBus
from faos.services.workflow.service import WorkflowService
from faos.services.capability.service import CapabilityService
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.execution.planner_models import PlannerResponse

logger = logging.getLogger(__name__)


class PlannerPipeline:
    def __init__(self, event_bus: EventBus, workflow_service: WorkflowService = None,
                 capability_service: CapabilityService = None, reasoning_service: ReasoningService = None):
        self.event_bus = event_bus
        self.workflow_service = workflow_service
        self.capability_service = capability_service
        self.reasoning_service = reasoning_service
        self.event_bus.subscribe("TaskSubmitted", self._handle_task_submitted)

    def _build_system_prompt(self, force: bool = False) -> str:
        """Build the system prompt for the Planner LLM, with awareness of conversational mode."""
        available_workflows = []
        if self.workflow_service:
            for wf_id, wf_def in self.workflow_service.workflows.items():
                available_workflows.append({
                    "id": wf_id,
                    "name": getattr(wf_def, "name", wf_id),
                    "description": getattr(wf_def, "description", "No description available")
                })

        force_clause = ""
        if force:
            force_clause = (
                "\n\nIMPORTANT: The user has requested FORCE EXECUTION. "
                "You MUST output status='ready' no matter what. "
                "If any required parameters are missing, infer reasonable defaults "
                "(e.g. if no stock is specified, pick a well-known benchmark like 'AAPL' or '000001.SS'). "
                "Do NOT output status='clarify' when force is true."
            )

        return (
            "# Your Identity\n"
            "You are **FAOS Planner** — a highly intelligent, friendly, and professional AI financial analyst assistant. "
            "You are the first point of contact for users entering the FAOS Trading Agents platform.\n\n"
            "## Your Personality\n"
            "- You are warm, approachable, and conversational — like a knowledgeable friend who works on Wall Street.\n"
            "- When the user greets you casually (e.g. 'hi', 'hello', '你好'), respond naturally with a greeting "
            "and briefly introduce what you can do (analyze stocks, backtest strategies, summarize market news, etc.). "
            "Do NOT immediately demand a stock ticker. Be human.\n"
            "- When the user asks a general question, answer it helpfully and steer the conversation towards actionable analysis.\n"
            "- Always match the user's language. If they write in Chinese, respond entirely in Chinese. "
            "If they write in English, respond in English. If they mix, follow the dominant language.\n\n"
            "## Your Core Job\n"
            "You operate in a CONVERSATIONAL mode. Your job is to:\n"
            "1. Understand the user's intent through natural dialogue.\n"
            "2. When you have enough information to start analysis, output status='ready' with extracted parameters.\n"
            "3. When information is missing or ambiguous, output status='clarify' and ask a targeted question naturally.\n\n"
            "## Decision Logic for 'clarify' vs 'ready':\n"
            "- If the user clearly specifies an analysis target (a stock, company name, or market), output status='ready'.\n"
            "- If the user is just chatting, greeting, or asking what you can do, output status='clarify' "
            "with a friendly conversational response (NOT a cold demand for parameters).\n"
            "- If the user says something vague like '帮我分析下' or 'analyze something', gently ask what they'd like to focus on.\n"
            "- NEVER respond with robotic error messages. You are an AI with personality.\n\n"
            "## Ticker Symbol Rules:\n"
            "For the 'symbol' parameter, output a standard Yahoo Finance ticker symbol. "
            "Translate company names to tickers (e.g. 'Apple' → 'AAPL', '宝丰能源' → '600989.SS'). "
            "Chinese A-shares: '.SS' (Shanghai) or '.SZ' (Shenzhen). "
            "Hong Kong: '.HK'. US stocks: base ticker only (no '.O').\n\n"
            "## Parameter Extraction:\n"
            "Analyze the user's FULL intent. If they mention language preference, output format, "
            "analysis angle, or time horizon, capture all of these in the parameters dict.\n\n"
            f"## Available Workflows:\n{json.dumps(available_workflows, ensure_ascii=False, indent=2)}\n"
            f"{force_clause}\n\n"
            "## Response Format\n"
            "You MUST respond in valid JSON:\n"
            "{\n"
            '  "status": "clarify" or "ready",\n'
            '  "message": "your natural, conversational response to the user",\n'
            '  "workflow_id": "string (required if ready, null if clarify)",\n'
            '  "parameters": {"key": "value"},\n'
            '  "reasoning": "your internal reasoning (not shown to user)"\n'
            "}"
        )

    async def chat(self, messages: List[Dict[str, str]], force: bool = False,
                   llm_config: Dict[str, Any] = None) -> PlannerResponse:
        """
        Conversational Planner entry point.
        
        Args:
            messages: List of {"role": "user"|"assistant", "content": "..."} dicts.
            force: If True, Planner MUST return status='ready', filling in missing params.
            llm_config: LLM configuration (provider, model, api_key).
        
        Returns:
            PlannerResponse with status='clarify' or 'ready'.
        """
        if not self.reasoning_service:
            return PlannerResponse(
                status="ready",
                message="Reasoning service not available, using defaults.",
                workflow_id="AnalyzeStockWorkflow",
                parameters={"symbol": "AAPL"}
            )

        system_prompt = self._build_system_prompt(force=force)

        # Build conversation context for the LLM
        conversation_text = ""
        for msg in messages:
            role_label = "User" if msg["role"] == "user" else "Planner"
            conversation_text += f"[{role_label}]: {msg['content']}\n"

        context_data = {
            "conversation_history": conversation_text,
        }

        req = ReasoningRequest(
            task_id="planner-chat",
            prompt=system_prompt,
            context_data=context_data,
            model="gemini-3.5-flash",
            llm_config=llm_config
        )

        resp = await self.reasoning_service.analyze_context(req)

        # Parse LLM response
        try:
            raw_response = resp.raw_response
            start = raw_response.find("{")
            end = raw_response.rfind("}")
            if start != -1 and end != -1:
                json_str = raw_response[start:end + 1]
                data = json.loads(json_str)
                result = PlannerResponse(**data)
                logger.info(f"Planner chat response: status={result.status}, wf={result.workflow_id}, params={result.parameters}")
                return result
        except Exception as e:
            logger.error(f"Planner failed to parse LLM chat response: {e}. Raw: {resp.raw_response[:300]}")

        # Fallback: if force, return ready with defaults; otherwise a friendly clarify
        if force:
            return PlannerResponse(
                status="ready",
                message="好的，我将为您启动默认分析流程。",
                workflow_id="AnalyzeStockWorkflow",
                parameters={"symbol": "AAPL"}
            )
        else:
            # Detect language from last user message for a natural fallback
            last_msg = messages[-1]["content"] if messages else ""
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in last_msg)
            if is_chinese:
                fallback_msg = (
                    "你好！👋 我是 FAOS 智能投研助手，很高兴见到你！\n\n"
                    "我可以帮你做这些事情：\n"
                    "• 📊 **深度分析**一只股票（A股、港股、美股都支持）\n"
                    "• 📰 **汇总市场新闻**和热点\n"
                    "• 🔄 **回测交易策略**\n\n"
                    "你想分析哪只股票或者了解什么？直接告诉我就好 😊"
                )
            else:
                fallback_msg = (
                    "Hey there! 👋 I'm the FAOS AI Trading Analyst — great to meet you!\n\n"
                    "Here's what I can help you with:\n"
                    "• 📊 **Deep analysis** of any stock (US, HK, China A-shares)\n"
                    "• 📰 **Market news** summaries & sentiment\n"
                    "• 🔄 **Backtest** trading strategies\n\n"
                    "What would you like to explore? Just tell me a stock or topic! 😊"
                )
            return PlannerResponse(
                status="clarify",
                message=fallback_msg
            )

    async def _handle_task_submitted(self, event: Event):
        """
        Legacy event handler. When a task is submitted directly (bypassing chat),
        this runs the planner in force mode to guarantee execution.
        """
        task_id = event.payload.get("task_id")
        intent = event.payload.get("intent", "")
        llm_config = event.payload.get("llm_config")

        logger.info(f"Planner processing Task {task_id} with intent: {intent}")

        if not self.workflow_service or not self.reasoning_service:
            logger.error("WorkflowService or ReasoningService is not initialized in PlannerPipeline")
            return

        # Use the chat method in force mode to guarantee a 'ready' response
        messages = [{"role": "user", "content": intent}]
        planner_result = await self.chat(messages, force=True, llm_config=llm_config)

        workflow_id = planner_result.workflow_id or "AnalyzeStockWorkflow"
        params = planner_result.parameters or {"symbol": "AAPL"}

        workflow_def = self.workflow_service.get_workflow(workflow_id)
        if not workflow_def:
            logger.warning(f"Workflow '{workflow_id}' not found, falling back to 'AnalyzeStockWorkflow'")
            workflow_id = "AnalyzeStockWorkflow"
            workflow_def = self.workflow_service.get_workflow(workflow_id)
            if not workflow_def:
                logger.error("Fallback Workflow 'AnalyzeStockWorkflow' not found.")
                return

        # Execution Plan Generation
        plan_nodes = []
        for w_node in workflow_def.nodes:
            node_params = params.copy()
            plan_nodes.append(PlanNode(
                id=w_node.id,
                capability=w_node.capability,
                parameters=node_params,
                dependencies=w_node.dependencies
            ))

        plan = ExecutionPlan(
            task_id=task_id,
            nodes=plan_nodes
        )

        plan_event = Event(
            type="ExecutionPlanGenerated",
            source="PlannerPipeline",
            payload={"task_id": task_id, "plan": plan.model_dump()}
        )

        await self.event_bus.publish(plan_event)
        logger.info(f"Planner generated ExecutionPlan for Task {task_id} using {workflow_id}")
