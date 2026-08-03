import asyncio
import logging
from typing import List

from faos.services.discussion.models import (
    DiscussionRequest, DiscussionResponse, AgentOpinion,
    BullCase, BearCase, DebateJudgment, RiskGuard,
    BULL_CASE_JSON_HINT, BEAR_CASE_JSON_HINT, DEBATE_JUDGMENT_JSON_HINT,
    RISK_GUARD_JSON_HINT,
)
from faos.services.prompting import registry
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest

logger = logging.getLogger(__name__)

class DiscussionService:
    """
    Discussion Service coordinates multi-stage debates (Investment Debate, Risk Debate).
    """
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning = reasoning_service
        logger.info("DiscussionService initialized with multi-stage debate roles")

    async def discuss_stage(self, request: DiscussionRequest, stage: str, context) -> DiscussionResponse:
        """
        Executes a specific discussion stage based on the DAG node execution.
        """
        logger.info(f"DiscussionService executing stage {stage} for task {request.task_id}")
        opinions: List[AgentOpinion] = []
        lang = (request.context_data.get("user_parameters", {}) or {}).get("language", "zh")
        
        try:
            if stage == "stage1":
                # Stage 1: Bull vs Bear
                return await self._run_stage1(request, lang, context)
            elif stage == "stage2":
                # Stage 2: Manager
                return await self._run_stage2(request, lang, context)
            elif stage == "stage3":
                # Stage 3: Mastermind Debate
                return await self._run_stage3(request, lang, context)
            elif stage == "stage4":
                # Stage 4: CRO & Strategist
                return await self._run_stage4(request, lang, context)
            else:
                return DiscussionResponse(status="failed", error=f"Unknown discuss_stage {stage}")
        except Exception as e:
            import traceback
            logger.error(f"Discussion stage {stage} failed: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            return DiscussionResponse(status="failed", error=f"{type(e).__name__}: {str(e)}")

    async def _run_stage1(self, request: DiscussionRequest, lang: str, context) -> DiscussionResponse:
        opinions: List[AgentOpinion] = []
        # Stage 1a: Bull Researcher -> numbered, attackable Claims
        bull_prompt = registry.render_prompt(
            "bull_researcher", 
            context_data=request.context_data, 
            language=lang,
            json_hint=BULL_CASE_JSON_HINT
        )
        bull_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=dict(request.context_data),
            prompt=bull_prompt,
            llm_config=request.llm_config,
            is_rendered=True,
            enable_tools=True,
        )
        bull_case, bull_raw = await self.reasoning.analyze_structured(bull_req, BullCase)
        if bull_case is None: bull_case = BullCase(summary=bull_raw)
        
        bull_conf = sum(c.confidence for c in bull_case.claims) / len(bull_case.claims) if bull_case.claims else 0.5
        opinions.append(AgentOpinion(
            name="Bull Researcher", role="debator",
            opinion=bull_case.render(lang), confidence=bull_conf,
            structured=bull_case.model_dump()
        ))
        
        # Stage 1b: Bear Researcher
        bear_context = dict(request.context_data)
        bear_context["bull_claims"] = [c.model_dump() for c in bull_case.claims]
        bear_context["bull_summary"] = bull_case.summary
        bear_prompt = registry.render_prompt(
            "bear_researcher", 
            context_data=bear_context, 
            language=lang,
            json_hint=BEAR_CASE_JSON_HINT
        )
        bear_req = ReasoningRequest(
            task_id=request.task_id,
            context_data=bear_context,
            prompt=bear_prompt,
            llm_config=request.llm_config,
            is_rendered=True,
            enable_tools=True,
        )
        bear_case, bear_raw = await self.reasoning.analyze_structured(bear_req, BearCase)
        if bear_case is None: bear_case = BearCase(summary=bear_raw)
        
        bear_conf = sum(r.strength for r in bear_case.rebuttals) / len(bear_case.rebuttals) if bear_case.rebuttals else 0.5
        opinions.append(AgentOpinion(
            name="Bear Researcher", role="debator",
            opinion=bear_case.render(lang), confidence=bear_conf,
            structured=bear_case.model_dump()
        ))
        
        return DiscussionResponse(status="success", consensus="Stage 1 complete", opinions=opinions)

    async def _run_stage2(self, request: DiscussionRequest, lang: str, context) -> DiscussionResponse:
        opinions: List[AgentOpinion] = []
        # Extract bull and bear cases from previous stage (stage1)
        # Using context.results
        prev_disc = context.results.get("discussion", {})
        
        bull_case_struct = {}
        bear_case_struct = {}
        # In a fully unrolled DAG, we need to extract from context.results or context.evidence
        # For simplicity, if we get it from context.results, it's unstructured string, but we want structured data.
        # Actually, let's just do a simplified context mapping or rely on what's available.
        # Wait, the monolith passes structured objects. If we split into DAG nodes, we must serialize them.
        # To avoid over-complicating state passing, if the frontend needs `node4_s1` etc, 
        # we can just use `request.context.get_variable` or `add_result` to pass state.
        
        # Pull state from Context
        s1_ops = context.results.get("stage1_ops", [])
        bull_case = next((o for o in s1_ops if o["name"] == "Bull Researcher"), {}).get("structured", {})
        bear_case = next((o for o in s1_ops if o["name"] == "Bear Researcher"), {}).get("structured", {})
        
        judge_context = {
            "bull_claims": bull_case.get("claims", []),
            "bull_summary": bull_case.get("summary", ""),
            "bear_rebuttals": bear_case.get("rebuttals", []),
            "bear_extra_risks": bear_case.get("extra_risks", []),
            "bear_summary": bear_case.get("summary", ""),
            "user_parameters": request.context_data.get("user_parameters", {}),
            "quote": request.context_data.get("quote", {}),
            "fact_sheet": request.context_data.get("fact_sheet", {}),
            "news": request.context_data.get("news", []),
            "analysis_reports": request.context_data.get("analysis_reports", {}),
        }
        mgr_prompt = registry.render_prompt(
            "professional_reviewer", 
            context_data=judge_context, 
            language=lang,
            json_hint=DEBATE_JUDGMENT_JSON_HINT
        )
        mgr_req = ReasoningRequest(
            task_id=request.task_id, context_data=judge_context,
            prompt=mgr_prompt, llm_config=request.llm_config,
            is_rendered=True, enable_tools=True,
        )
        judgment, mgr_raw = await self.reasoning.analyze_structured(mgr_req, DebateJudgment)
        if judgment is None: judgment = DebateJudgment(investment_plan=mgr_raw)
        
        opinions.append(AgentOpinion(
            name="Research Manager", role="research_manager",
            opinion=judgment.render(lang), confidence=judgment.overall_confidence,
            structured=judgment.model_dump()
        ))
        return DiscussionResponse(status="success", consensus="Stage 2 complete", opinions=opinions)

    async def _run_stage3(self, request: DiscussionRequest, lang: str, context) -> DiscussionResponse:
        opinions: List[AgentOpinion] = []
        # Mastermind & Risk Debate
        s2_ops = context.results.get("stage2_ops", [])
        investment_plan = next((o for o in s2_ops if o["name"] == "Research Manager"), {}).get("opinion", "")
        
        risk_context = request.context_data.copy()
        risk_context["investment_plan"] = investment_plan
        
        prompts = {
            "Aggressive Risk Debator": registry.render_prompt("aggressive_risk_analyst", context_data=risk_context, language=lang),
            "Conservative Risk Debator": registry.render_prompt("conservative_risk_analyst", context_data=risk_context, language=lang),
            "Neutral Risk Debator": registry.render_prompt("neutral_risk_analyst", context_data=risk_context, language=lang),
            "Risk Manager": registry.render_prompt("risk_manager", context_data=risk_context, language=lang),
            "Value Investing Sage": registry.render_prompt("value_investing_sage", context_data=risk_context, language=lang),
            "Contrarian Strategist": registry.render_prompt("contrarian_strategist", context_data=risk_context, language=lang),
            "Macro Hedge Titan": registry.render_prompt("macro_hedge_titan", context_data=risk_context, language=lang),
            "Soros Style Philosopher": registry.render_prompt("soros_style_financial_philosopher", context_data=risk_context, language=lang),
        }
        
        risk_opinions = await self._run_parallel_agents(request, prompts, base_context=risk_context)
        opinions.extend(risk_opinions)
        return DiscussionResponse(status="success", consensus="Stage 3 complete", opinions=opinions)

    async def _run_stage4(self, request: DiscussionRequest, lang: str, context) -> DiscussionResponse:
        opinions: List[AgentOpinion] = []
        
        s2_ops = context.results.get("stage2_ops", [])
        investment_plan = next((o for o in s2_ops if o["name"] == "Research Manager"), {}).get("opinion", "")
        
        s3_ops = context.results.get("stage3_ops", [])
        risk_debate = "\n".join([o.get("opinion", "") for o in s3_ops])
        
        # CRO
        risk_debate_context = request.context_data.copy()
        risk_debate_context["investment_plan"] = investment_plan
        risk_debate_context["risk_debate"] = risk_debate
        
        cro_prompt = registry.render_prompt(
            "chief_audit_officer", 
            context_data=risk_debate_context, 
            language=lang,
            json_hint=RISK_GUARD_JSON_HINT
        )
        cro_req = ReasoningRequest(
            task_id=request.task_id, context_data=risk_debate_context,
            prompt=cro_prompt, llm_config=request.llm_config,
            is_rendered=True, enable_tools=True,
        )
        risk_guard, cro_raw = await self.reasoning.analyze_structured(cro_req, RiskGuard)
        if risk_guard is None: risk_guard = RiskGuard(notes=cro_raw)
        risk_plan = risk_guard.render(lang)
        opinions.append(AgentOpinion(
            name="Chief Risk Officer", role="chief_risk_officer",
            opinion=risk_plan, confidence=risk_guard.confidence,
            structured=risk_guard.model_dump()
        ))
        
        # Chief Strategist
        strat_context = request.context_data.copy()
        strat_context["investment_plan"] = investment_plan
        strat_context["risk_plan"] = risk_plan
        strat_context["risk_debate"] = risk_debate
        strat_context["cr_opinion"] = risk_plan
        
        strat_prompt = registry.render_prompt(
            "chief_strategist",
            context_data=strat_context,
            language=lang,
        )
        strat_req = ReasoningRequest(
            task_id=request.task_id, context_data=strat_context,
            prompt=strat_prompt, llm_config=request.llm_config,
            is_rendered=True, enable_tools=True,
        )
        strat_resp = await self.reasoning.analyze_context(strat_req)
        strategy = strat_resp.raw_response or "暂无法生成策略。"
        opinions.append(AgentOpinion(
            name="Chief Strategist", role="chief_strategist",
            opinion=strategy, confidence=0.75,
        ))
        
        consensus = (
            f"--- Investment Plan ---\n{investment_plan}\n\n"
            f"--- Risk Plan ---\n{risk_plan}\n\n"
            f"--- Strategy ---\n{strategy}"
        )
        return DiscussionResponse(status="success", consensus=consensus, opinions=opinions)

    async def discuss(self, request: DiscussionRequest) -> DiscussionResponse:
        logger.info(f"DiscussionService starting multi-stage debate for task {request.task_id}")
        opinions: List[AgentOpinion] = []
        lang = (request.context_data.get("user_parameters", {}) or {}).get("language", "zh")
        
        try:
            # Stage 1a: Bull Researcher -> numbered, attackable Claims
            bull_prompt = registry.render_prompt(
                "bull_researcher", 
                context_data=request.context_data, 
                language=lang,
                json_hint=BULL_CASE_JSON_HINT
            )
            bull_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=dict(request.context_data),
                prompt=bull_prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            bull_case, bull_raw = await self.reasoning.analyze_structured(
                bull_req, BullCase
            )
            if bull_case is None:
                bull_case = BullCase(summary=bull_raw)
            bull_conf = (
                sum(c.confidence for c in bull_case.claims) / len(bull_case.claims)
                if bull_case.claims else 0.5
            )
            opinions.append(AgentOpinion(
                name="Bull Researcher", role="debator",
                opinion=bull_case.render(lang), confidence=bull_conf,
                structured=bull_case.model_dump()
            ))
            
            # Stage 1b: Bear Researcher -> point-by-point rebuttals (SEES the bull's claims)
            bear_context = dict(request.context_data)
            bear_context["bull_claims"] = [c.model_dump() for c in bull_case.claims]
            bear_context["bull_summary"] = bull_case.summary
            bear_prompt = registry.render_prompt(
                "bear_researcher", 
                context_data=bear_context, 
                language=lang,
                json_hint=BEAR_CASE_JSON_HINT
            )
            bear_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=bear_context,
                prompt=bear_prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            bear_case, bear_raw = await self.reasoning.analyze_structured(
                bear_req, BearCase
            )
            if bear_case is None:
                bear_case = BearCase(summary=bear_raw)
            bear_conf = (
                sum(r.strength for r in bear_case.rebuttals) / len(bear_case.rebuttals)
                if bear_case.rebuttals else 0.5
            )
            opinions.append(AgentOpinion(
                name="Bear Researcher", role="debator",
                opinion=bear_case.render(lang), confidence=bear_conf,
                structured=bear_case.model_dump()
            ))
            
            # Stage 2: Research Manager JUDGES the debate (claims vs rebuttals)
            judge_context = {
                "bull_claims": [c.model_dump() for c in bull_case.claims],
                "bull_summary": bull_case.summary,
                "bear_rebuttals": [r.model_dump() for r in bear_case.rebuttals],
                "bear_extra_risks": [c.model_dump() for c in bear_case.extra_risks],
                "bear_summary": bear_case.summary,
                "user_parameters": request.context_data.get("user_parameters", {}),
                # Carry forward the full context so the manager has access to
                # quote, fact_sheet, news, and analysis reports for evidence.
                "quote": request.context_data.get("quote", {}),
                "fact_sheet": request.context_data.get("fact_sheet", {}),
                "news": request.context_data.get("news", []),
                "analysis_reports": request.context_data.get("analysis_reports", {}),
            }
            # The manager in ALSA is the professional_reviewer / critic
            mgr_prompt = registry.render_prompt(
                "professional_reviewer", 
                context_data=judge_context, 
                language=lang,
                json_hint=DEBATE_JUDGMENT_JSON_HINT
            )
            mgr_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=judge_context,
                prompt=mgr_prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            judgment, mgr_raw = await self.reasoning.analyze_structured(
                mgr_req, DebateJudgment
            )
            if judgment is None:
                judgment = DebateJudgment(investment_plan=mgr_raw)
            investment_plan = judgment.investment_plan or judgment.render(lang)
            
            opinions.append(AgentOpinion(
                name="Research Manager", role="research_manager",
                opinion=judgment.render(lang), confidence=judgment.overall_confidence,
                structured=judgment.model_dump()
            ))
            
            # Stage 3: Risk Debate (Aggressive, Conservative, Neutral, Risk Manager)
            risk_context = request.context_data.copy()
            risk_context["investment_plan"] = investment_plan
            
            risk_opinions = await self._run_parallel_agents(request, {
                "Aggressive Risk Debator": registry.render_prompt("aggressive_risk_analyst", context_data=risk_context, language=lang),
                "Conservative Risk Debator": registry.render_prompt("conservative_risk_analyst", context_data=risk_context, language=lang),
                "Neutral Risk Debator": registry.render_prompt("neutral_risk_analyst", context_data=risk_context, language=lang),
                "Risk Manager": registry.render_prompt("risk_manager", context_data=risk_context, language=lang),
            }, base_context=risk_context)
            opinions.extend(risk_opinions)
            
            # Stage 4: Chief Risk Officer -> structured RiskGuard (stop-loss / sizing / hedges)
            risk_debate_context = risk_context.copy()
            risk_debate_context["risk_debate"] = "\n".join([o.opinion for o in risk_opinions])
            
            cro_prompt = registry.render_prompt(
                "chief_audit_officer", 
                context_data=risk_debate_context, 
                language=lang,
                json_hint=RISK_GUARD_JSON_HINT
            )
            cro_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=risk_debate_context,
                prompt=cro_prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            risk_guard, cro_raw = await self.reasoning.analyze_structured(
                cro_req, RiskGuard
            )
            if risk_guard is None:
                risk_guard = RiskGuard(notes=cro_raw)
            risk_plan = risk_guard.render(lang)
            
            opinions.append(AgentOpinion(
                name="Chief Risk Officer", role="chief_risk_officer",
                opinion=risk_plan, confidence=risk_guard.confidence,
                structured=risk_guard.model_dump()
            ))
            
            # Stage 5: Chief Strategist — final strategic synthesis
            strat_context = request.context_data.copy()
            strat_context["investment_plan"] = investment_plan
            strat_context["risk_plan"] = risk_plan
            strat_context["risk_debate"] = "\n".join([o.opinion for o in risk_opinions])
            strat_context["cr_opinion"] = risk_plan
            
            strat_prompt = registry.render_prompt(
                "chief_strategist",
                context_data=strat_context,
                language=lang,
            )
            strat_req = ReasoningRequest(
                task_id=request.task_id,
                context_data=strat_context,
                prompt=strat_prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            strat_resp = await self.reasoning.analyze_context(strat_req)
            strategy = strat_resp.raw_response or "暂无法生成策略。"
            opinions.append(AgentOpinion(
                name="Chief Strategist", role="chief_strategist",
                opinion=strategy, confidence=0.75,
            ))
            
            # The consensus text combines all stages
            consensus = (
                f"--- Investment Plan ---\n{investment_plan}\n\n"
                f"--- Risk Plan ---\n{risk_plan}\n\n"
                f"--- Strategy ---\n{strategy}"
            )
            
            return DiscussionResponse(
                status="success",
                consensus=consensus,
                opinions=opinions
            )
            
        except Exception as e:
            import traceback
            return DiscussionResponse(status="failed", error=f"{type(e).__name__}: {str(e) if str(e) else '无错误消息'}")

    async def _run_parallel_agents(self, request: DiscussionRequest, agent_prompts: dict, base_context: dict = None) -> List[AgentOpinion]:
        context = base_context if base_context is not None else request.context_data
        tasks = []
        keys = []
        for name, prompt in agent_prompts.items():
            req = ReasoningRequest(
                task_id=request.task_id,
                context_data=context,
                prompt=prompt,
                llm_config=request.llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            tasks.append(self.reasoning.analyze_context(req))
            keys.append(name)
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        opinions = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Agent {keys[i]} failed: {res}")
                continue
            opinions.append(AgentOpinion(
                name=keys[i],
                role="debator",
                opinion=res.raw_response,
                confidence=res.confidence
            ))
        return opinions

