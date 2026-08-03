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
            "     - Set `parameters: {\"symbol\": \"<RESOLVED_TICKER>\", \"investment_horizon\": \"<short-term | long-term>\", \"strategic_focus\": \"<user specific focus, e.g., dividend, growth, risk>\"}`.\n"
            "   - **STRICT RULE**: When the user specifies a stock target alongside an analysis intent, NEVER ask for clarification! Output `status: 'ready'` immediately.\n\n"
            "2. **Market News & Macro Intelligence (`NewsSummaryWorkflow`)**:\n"
            "   - **Trigger**: The user asks for financial news, morning digests, macro trends, policy updates, central bank decisions, or geopolitics\n"
            "     (e.g., '全球财经新闻', '华尔街见闻早餐', '财联社早间新闻精选', '美联储降息政策', '央视新闻/统计局数据').\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'NewsSummaryWorkflow'`.\n"
            "   - **Search Strategy**: Set `parameters: {\"search_query\": \"...\", \"news_type\": \"...\"}` referencing authoritative domestic and global media (华尔街见闻, 财联社, 央视新闻, 新华社, Bloomberg, Reuters, CNBC, FT, WSJ, Goldman Sachs).\n\n"
            "3. **Strategy Backtest & Quantitative Analysis (`BacktestStrategyWorkflow`)**:\n"
            "   - **Trigger**: The user asks to test or backtest a trading strategy or quantitative signal.\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'BacktestStrategyWorkflow'`.\n\n"
            "4. **Sector Scanning & Stock Discovery (`SectorScanWorkflow`)**:\n"
            "   - **Trigger**: The user asks to find, screen, scan, or discover stocks in a specific sector or matching specific criteria (e.g., '帮我找找最近被低估的半导体股票', '有哪些优质的创新药标的', 'Screen for high dividend yield utility stocks').\n"
            "   - **Action**: Output `status: 'ready'`, `workflow_id: 'SectorScanWorkflow'`.\n"
            "   - **Parameters**: Set `parameters: {\"sector\": \"<target_sector>\", \"criteria\": \"<screening_criteria>\"}`.\n\n"
            "5. **Conversational Q&A / Greetings / General Guidance (`status: 'clarify'`)**:\n"
            "   - **Trigger**: The user greets you ('hi', 'hello', '你好'), asks general financial questions, or makes a vague request without any target ('帮我看下').\n"
            "   - **Action**: Output `status: 'clarify'`, provide an intelligent, helpful response matching the user's language, and guide them on what system capabilities they can run.\n\n"
            f"{force_clause}\n\n"
            "## JSON Output Format (STRICT)\n"
            "You MUST respond in valid JSON ONLY:\n"
            "{\n"
            '  "intent_analysis": "Detailed breakdown of what the user wants, involved entities, and required depth. Write this FIRST.",\n'
            '  "plan_steps": ["step 1", "step 2", "step 3..."],\n'
            '  "status": "ready" | "clarify",\n'
            '  "message": "natural, friendly response explaining your decision or asking for clarification",\n'
            '  "workflow_id": "workflow id if ready, null if clarify",\n'
            '  "parameters": {"symbol": "NVDA", "investment_horizon": "long-term", "strategic_focus": "AI chip market dominance"},\n'
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
            json_mode=True,
            model=(llm_config or {}).get("model"),
            llm_config=llm_config,
            enable_tools=True,
        )

        try:
            result = await self.reasoning_service.analyze_structured(req, response_model=PlannerResponse)
            if not result:
                # If exhausted retries and returned None
                logger.error("Planner failed to generate valid structured output after retries.")
                raise Exception("analyze_structured returned None")
            
            logger.info(f"Planner chat response: status={result.status}, wf={result.workflow_id}, params={result.parameters}")
            return result
            
        except Exception as e:
            logger.error(f"Planner error using analyze_structured: {e}")

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

        if workflow_id == "AnalyzeStockWorkflow":
            plan_nodes = self._build_dynamic_stock_plan(params)
        else:
            workflow_def = self.workflow_service.get_workflow(workflow_id)
            if not workflow_def:
                logger.warning(f"Workflow '{workflow_id}' not found, falling back to 'AnalyzeStockWorkflow'")
                workflow_id = "AnalyzeStockWorkflow"
                plan_nodes = self._build_dynamic_stock_plan(params)
            else:
                # Execution Plan Generation for Static Workflows
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

    def _build_dynamic_stock_plan(self, params: Dict[str, Any]) -> List[PlanNode]:
        """
        Dynamically construct the AnalyzeStock DAG based on the target market.
        Brings ALSA-style 'market awareness' and dynamic capabilities.
        """
        from faos.execution.market_detector import detect_market
        symbol = params.get("symbol", "AAPL")
        market = detect_market(symbol)
        
        node_params = params.copy()
        node_params["market"] = market
        
        # Inject ALSA-inspired specific analytical focuses
        market_focus = {
            "A-Share": "重点关注国内宏观政策导向、监管动态以及零售资金情绪 (Focus on domestic macro policy, regulations, and retail sentiment).",
            "HK-Share": "重点关注南向/外资流动性、地缘政治风险以及高股息特征 (Focus on liquidity, geopolitical risks, and dividend yield).",
            "US-Share": "重点关注美联储宏观利率、企业盈利增长以及技术创新周期 (Focus on Fed rates, earnings growth, and tech cycles)."
        }.get(market, "")
        
        if market_focus:
            node_params["market_focus"] = market_focus

        nodes = []
        # Parallel data prefetch (Data and News)
        nodes.append(PlanNode(id="node1", capability="cap.fetch_data", parameters=node_params, dependencies=[]))
        nodes.append(PlanNode(id="node2", capability="cap.fetch_news", parameters=node_params, dependencies=[]))
        
        # Analyze Pipeline DAG
        # Stage 1: Core
        p1 = node_params.copy()
        p1["analyze_stage"] = 1
        nodes.append(PlanNode(id="node3_s1", capability="cap.analyze", parameters=p1, dependencies=["node1", "node2"]))
        
        # Stage 2: Perspectives
        p2 = node_params.copy()
        p2["analyze_stage"] = 2
        nodes.append(PlanNode(id="node3_s2", capability="cap.analyze", parameters=p2, dependencies=["node3_s1"]))
        
        # Stage 3: Professional Reviewer
        p3 = node_params.copy()
        p3["analyze_stage"] = 3
        nodes.append(PlanNode(id="node3_s3", capability="cap.analyze", parameters=p3, dependencies=["node3_s2"]))
        
        # Stage 4: Chief Strategist
        p4 = node_params.copy()
        p4["analyze_stage"] = 4
        nodes.append(PlanNode(id="node3_s4", capability="cap.analyze", parameters=p4, dependencies=["node3_s3"]))
        
        # Discussion Pipeline DAG
        # Stage 1: Bull vs Bear
        d1 = node_params.copy()
        d1["discuss_stage"] = "stage1"
        nodes.append(PlanNode(id="node_discuss_s1", capability="cap.discuss", parameters=d1, dependencies=["node3_s4"]))
        
        # Stage 2: Manager
        d2 = node_params.copy()
        d2["discuss_stage"] = "stage2"
        nodes.append(PlanNode(id="node_discuss_s2", capability="cap.discuss", parameters=d2, dependencies=["node_discuss_s1"]))
        
        # Stage 3: Mastermind Debate
        d3 = node_params.copy()
        d3["discuss_stage"] = "stage3"
        nodes.append(PlanNode(id="node_discuss_s3", capability="cap.discuss", parameters=d3, dependencies=["node_discuss_s2"]))
        
        # Stage 4: CRO & Strategy
        d4 = node_params.copy()
        d4["discuss_stage"] = "stage4"
        nodes.append(PlanNode(id="node_discuss_s4", capability="cap.discuss", parameters=d4, dependencies=["node_discuss_s3"]))
        
        nodes.append(PlanNode(id="node_decision", capability="cap.decision", parameters=node_params, dependencies=["node_discuss_s4"]))
        nodes.append(PlanNode(id="node_reflection", capability="cap.reflection", parameters=node_params, dependencies=["node_decision"]))
        nodes.append(PlanNode(id="node4", capability="cap.report", parameters=node_params, dependencies=["node_reflection"]))
        
        return nodes
