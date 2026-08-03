import asyncio
import logging
import traceback
from typing import List, Optional
from faos.services.analyze.models import AnalyzeRequest, AnalyzeResponse
from faos.services.prompting import registry
from faos.services.reasoning.service import ReasoningService
from faos.services.reasoning.models import ReasoningRequest
from faos.services.reasoning.schemas import AnalystReport, ANALYST_REPORT_JSON_HINT
from faos.services.security.grounding import verify_and_annotate
from faos.services.security.guardrail import check_guardrails

logger = logging.getLogger(__name__)

# ── Analyst group definitions ──────────────────────────────────────

STAGE1_CORE = ["fundamental_analyst", "technical_analyst", "sentiment_analyst"]
STAGE2_PERSPECTIVE = [
    "value_investing_sage",
    "growth_visionary",
    "contrarian_strategist",
    "macro_hedge_titan",
    "soros-style_financial_philosopher",
    "serenity_alpha_analyst",
    "deep_research_specialist",
]
STAGE3_REVIEWER = ["professional_reviewer"]
STAGE4_CHIEF = ["chief_strategist"]

# All available for user selection
ALL_ANALYSTS = STAGE1_CORE + STAGE2_PERSPECTIVE

# Default selected (stage 2 only; stage 1 is always on)
DEFAULT_STAGE2_SELECTED = list(STAGE2_PERSPECTIVE)


class AnalyzeService:
    def __init__(self, reasoning_service: ReasoningService):
        self.reasoning_service = reasoning_service

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        """Run the analysis pipeline. If target_stage is specified in user_parameters,
        only that stage is run. Otherwise, runs all 4 stages sequentially.
        """
        user_params = request.context_data.get("user_parameters", {}) or {}
        lang = user_params.get("language", "zh")
        target_stage = user_params.get("analyze_stage")

        stage2_selected = user_params.get("analyst_stage2", DEFAULT_STAGE2_SELECTED)
        if not isinstance(stage2_selected, list):
            stage2_selected = DEFAULT_STAGE2_SELECTED

        all_reports: dict = {}
        all_structured: dict = {}

        # ---------------- Stage 1 ----------------
        if target_stage is None or target_stage == 1:
            stage1_results = await self._run_stage(
                stage=1, role_names=STAGE1_CORE, context_data=request.context_data,
                lang=lang, task_id=request.task_id, llm_config=request.llm_config,
            )
            all_reports.update(stage1_results["rendered"])
            all_structured.update(stage1_results["structured"])
        else:
            stage1_results = {"structured": request.context_data.get("stage1_analysis", {})}

        # ---------------- Stage 2 ----------------
        if target_stage is None or target_stage == 2:
            stage2_context = dict(request.context_data)
            stage2_context["stage1_analysis"] = stage1_results["structured"]
            stage2_context["stage1_summaries"] = {
                k: (v.summary or "")[:300] if hasattr(v, "summary") else str(v)[:300]
                for k, v in stage1_results["structured"].items()
            }
            stage2_results = await self._run_stage(
                stage=2, role_names=stage2_selected, context_data=stage2_context,
                lang=lang, task_id=request.task_id, llm_config=request.llm_config,
            )
            all_reports.update(stage2_results["rendered"])
            all_structured.update(stage2_results["structured"])
        else:
            stage2_results = {"structured": request.context_data.get("stage2_analysis", {})}

        # ---------------- Stage 3 ----------------
        if target_stage is None or target_stage == 3:
            stage3_context = dict(request.context_data)
            stage3_context["stage1_analysis"] = stage1_results["structured"]
            stage3_context["stage2_analysis"] = stage2_results["structured"]
            stage3_context["all_summaries"] = {
                **{f"S1-{k}": (v.summary or "")[:200] if hasattr(v, "summary") else str(v)[:200] for k, v in stage1_results["structured"].items()},
                **{f"S2-{k}": (v.summary or "")[:200] if hasattr(v, "summary") else str(v)[:200] for k, v in stage2_results["structured"].items()},
            }
            stage3_results = await self._run_stage(
                stage=3, role_names=STAGE3_REVIEWER, context_data=stage3_context,
                lang=lang, task_id=request.task_id, llm_config=request.llm_config,
            )
            all_reports.update(stage3_results["rendered"])
            all_structured.update(stage3_results["structured"])
        else:
            stage3_results = {"structured": request.context_data.get("stage3_analysis", {})}

        # ---------------- Stage 4 ----------------
        if target_stage is None or target_stage == 4:
            stage4_context = dict(request.context_data)
            # Context Compression: DO NOT pass full stage1 and stage2 to stage4!
            stage4_context["stage3_analysis"] = stage3_results["structured"]
            stage4_context["all_summaries"] = {
                **{f"S1-{k}": (v.summary or "")[:200] if hasattr(v, "summary") else str(v)[:200] for k, v in stage1_results["structured"].items()},
                **{f"S2-{k}": (v.summary or "")[:200] if hasattr(v, "summary") else str(v)[:200] for k, v in stage2_results["structured"].items()},
                **{f"S3-{k}": (v.summary or "")[:200] if hasattr(v, "summary") else str(v)[:200] for k, v in stage3_results["structured"].items()},
            }
            stage4_results = await self._run_stage(
                stage=4, role_names=STAGE4_CHIEF, context_data=stage4_context,
                lang=lang, task_id=request.task_id, llm_config=request.llm_config,
            )
            all_reports.update(stage4_results["rendered"])
            all_structured.update(stage4_results["structured"])

        return AnalyzeResponse(
            task_id=request.task_id,
            status="success",
            analyst_reports=all_reports,
            structured_reports=all_structured,
        )

    async def _run_stage(
        self,
        stage: int,
        role_names: List[str],
        context_data: dict,
        lang: str,
        task_id: str,
        llm_config: Optional[dict] = None,
    ) -> dict:
        """Run one stage of analysts in parallel, returning rendered + structured results."""
        tasks = []
        for role_name in role_names:
            try:
                prompt = registry.render_prompt(
                    role_name,
                    context_data=context_data,
                    language=lang,
                    json_hint=ANALYST_REPORT_JSON_HINT,
                )
            except FileNotFoundError:
                logger.warning(f"Template for {role_name} not found. Skipping.")
                continue

            req = ReasoningRequest(
                task_id=task_id,
                context_data=dict(context_data),
                prompt=prompt,
                llm_config=llm_config,
                is_rendered=True,
                enable_tools=True,
            )
            tasks.append(self._run_analyst(role_name, req))

        if not tasks:
            logger.warning(f"Stage {stage}: no valid analysts, returning empty results.")
            return {"rendered": {}, "structured": {}}

        logger.info(f"Stage {stage}: running {len(tasks)} analysts in parallel: {role_names}")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        rendered = {}
        structured = {}
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"Stage {stage} gather exception: {type(res).__name__}: {res}\n{traceback.format_exc()}")
                continue
            rendered[res["name"]] = res["rendered"]
            structured[res["name"]] = res["structured"]

        return {"rendered": rendered, "structured": structured}

    async def _run_analyst(self, name: str, req: ReasoningRequest):
        lang = (req.context_data.get("user_parameters", {}) or {}).get("language", "zh")
        try:
            report, raw = await self.reasoning_service.analyze_structured(
                req, AnalystReport
            )
            if report is None:
                report = AnalystReport(summary=raw)

            report.role = name

            # 1. Output Guardrail (Logic interception)
            guard_res = check_guardrails(report)
            if guard_res.action == "block":
                logger.warning(f"Guardrail blocked output from {name}: {guard_res.reason}")
                report.summary = (
                    f"> [!CAUTION]\n> **[FAOS Guardrail Blocked]** 该分析结论未通过安全校验，已被强行拦截。\n"
                    f"> **拦截原因**: {guard_res.reason}\n\n"
                    f"~~{report.summary}~~"
                )
                report.action = "watch"

            # 2. Grounding Verifier (Anti-hallucination)
            fact_sheet = req.context_data.get("fact_sheet", {})
            report.summary = verify_and_annotate(report.summary, fact_sheet)

            return {
                "name": name,
                "structured": report,
                "rendered": report.render(lang),
            }
        except Exception as e:
            logger.error(
                f"Analyst {name} failed: {type(e).__name__}: {e}\n{traceback.format_exc()}"
            )
            stub = AnalystReport(
                summary=f"[分析失败] {name}: {type(e).__name__}: {str(e)[:300] if str(e) else '无错误消息'}",
                confidence=0.0,
            )
            stub.role = name
            return {"name": name, "structured": stub, "rendered": stub.render(lang)}
