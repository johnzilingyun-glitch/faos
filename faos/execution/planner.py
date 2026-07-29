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
        """Build the dynamic system prompt for the Planner LLM with System Capabilities and Workflows."""
        available_workflows = []
        if self.workflow_service:
            for wf_id, wf_def in self.workflow_service.workflows.items():
                available_workflows.append({
                    "id": wf_id,
                    "name": getattr(wf_def, "name", wf_id),
                    "description": getattr(wf_def, "description", "No description available")
                })

        available_capabilities = []
        if self.capability_service:
            for cap_id, cap_manifest in self.capability_service.list_capabilities().items():
                available_capabilities.append({
                    "id": cap_id,
                    "name": cap_manifest.name,
                    "description": cap_manifest.description
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
            "# Role & Core Purpose\n"
            "You are **FAOS Planner** — an autonomous financial AI reasoning engine & intent supervisor for the FAOS Multi-Agent Trading Platform.\n"
            "Your job is to understand the user's conversation, analyze their intent, match their request to the platform's system capabilities "
            "and workflows, and autonomously determine whether to trigger an analysis pipeline (`status: 'ready'`) or respond naturally/ask clarifying questions (`status: 'clarify'`).\n\n"
            "## Registered System Capabilities Catalog\n"
            "The platform provides the following underlying capabilities:\n"
            f"{json.dumps(available_capabilities, ensure_ascii=False, indent=2)}\n\n"
            "## Available Executable Workflows Catalog\n"
            "The platform supports the following workflows:\n"
            f"{json.dumps(available_workflows, ensure_ascii=False, indent=2)}\n\n"
            "## Intent Recognition & Routing Rules\n"
            "Analyze the conversation history and classify the user's intent into one of the following categories:\n\n"
            "1. **Single Stock / Company / Asset Deep Research (`AnalyzeStockWorkflow`)**:\n"
            "   - **Trigger**: The user asks to analyze, research, check, or evaluate ANY specific company, stock name, ticker, or asset\n"
            "     (e.g., '分析美股 英伟达', '深度看下特斯拉', '查下腾讯', '分析 AAPL', '评估贵州茅台', 'look into NVDA', '分析一下三体概念股').\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'AnalyzeStockWorkflow'`.\n"
            "   - **Ticker Resolution Requirement**: Autonomously translate ANY company, brand, or stock name (in ANY language) into a standard Yahoo Finance ticker symbol:\n"
            "     - US Stocks: base ticker symbol (e.g. 英伟达/Nvidia → 'NVDA', 苹果/Apple → 'AAPL', 特斯拉/Tesla → 'TSLA', 微软 → 'MSFT', 谷歌 → 'GOOGL', 阿里 → 'BABA', 蔚来 → 'NIO').\n"
            "     - Hong Kong Stocks: 4-digit ticker + '.HK' (e.g. 腾讯 → '0700.HK', 美团 → '3690.HK', 百度 → '9888.HK').\n"
            "     - China A-Shares: 6-digit ticker + '.SS' (Shanghai) or '.SZ' (Shenzhen) (e.g. 贵州茅台 → '600519.SS', 宁德时代 → '300750.SZ').\n"
            "     - Set `parameters: {\"symbol\": \"<RESOLVED_TICKER>\"}`.\n"
            "   - **STRICT RULE**: When the user specifies a stock target alongside an analysis intent, NEVER ask for clarification! Output `status: 'ready'` immediately.\n\n"
            "2. **Market News & Macro Intelligence (`NewsSummaryWorkflow`)**:\n"
            "   - **Trigger**: The user asks for financial news, morning digests, macro trends, policy updates, central bank decisions, or geopolitics\n"
            "     (e.g., '全球财经新闻', '华尔街见闻早餐', '财联社早间新闻精选', '美联储降息政策', '央视新闻/统计局数据').\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'NewsSummaryWorkflow'`.\n"
            "   - **Search Strategy**: Set `parameters: {\"search_query\": \"...\", \"news_type\": \"...\"}` referencing authoritative domestic and global media (华尔街见闻, 财联社, 央视新闻, 新华社, Bloomberg, Reuters, CNBC, FT, WSJ, Goldman Sachs).\n\n"
            "3. **Strategy Backtest & Quantitative Analysis (`BacktestStrategyWorkflow`)**:\n"
            "   - **Trigger**: The user asks to test or backtest a trading strategy or quantitative signal.\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'BacktestStrategyWorkflow'`.\n\n"
            "4. **Conversational Q&A / Greetings / General Guidance (`status: 'clarify'`)**:\n"
            "   - **Trigger**: The user greets you ('hi', 'hello', '你好'), asks general financial questions, or makes a vague request without any target ('帮我看下').\n"
            "   - **Action**: Output `status: 'clarify'`, provide an intelligent, helpful response matching the user's language, and guide them on what system capabilities they can run.\n\n"
            f"{force_clause}\n\n"
            "## JSON Output Format (STRICT)\n"
            "You MUST respond in valid JSON ONLY:\n"
            "{\n"
            '  "status": "ready" | "clarify",\n'
            '  "message": "natural, friendly response explaining your decision or asking for clarification",\n'
            '  "workflow_id": "workflow id if ready, null if clarify",\n'
            '  "parameters": {"symbol": "NVDA"},\n'
            '  "reasoning": "step-by-step intent reasoning"\n'
            "}"
        )

    async def chat(self, messages: List[Dict[str, str]], force: bool = False,
                   llm_config: Dict[str, Any] = None) -> PlannerResponse:
        """
        Conversational Planner entry point.
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
            model=(llm_config or {}).get("model"),
            llm_config=llm_config
        )

        resp = await self.reasoning_service.analyze_context(req)
        raw_response = resp.raw_response or ""

        # Handle explicit LLM errors (e.g. 429 Rate Limit) without masking them as fake greetings
        if raw_response.startswith("[LLM Error]"):
            logger.error(f"Planner LLM returned error: {raw_response}")
            return PlannerResponse(
                status="clarify",
                message=f"⚠️ LLM 服务调用未成功:\n{raw_response}\n\n👉 请在右上角 ⚙️【设置】中检查 API Key 或切换 Provider/Model。"
            )

        # Parse LLM response JSON
        try:
            start = raw_response.find("{")
            end = raw_response.rfind("}")
            if start != -1 and end != -1:
                json_str = raw_response[start:end + 1]
                data = json.loads(json_str)
                result = PlannerResponse(**data)
                logger.info(f"Planner chat response: status={result.status}, wf={result.workflow_id}, params={result.parameters}")
                return result
        except Exception as e:
            logger.error(f"Planner failed to parse LLM chat response: {e}. Raw: {raw_response[:300]}")

        # Fallback: if force, return ready with defaults; otherwise a friendly clarify
        if force:
            return PlannerResponse(
                status="ready",
                message="好的，我将为您启动默认分析流程。",
                workflow_id="AnalyzeStockWorkflow",
                parameters={"symbol": "AAPL"}
            )
        else:
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
