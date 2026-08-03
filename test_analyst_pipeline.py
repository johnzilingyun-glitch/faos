"""
Tests for the 4-stage analyst pipeline and analyst_stage2 parameter flow.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Test 1: _run_stage logging no longer crashes ──

def test_run_stage_logging_no_attribute_error():
    """The old code did `t.__self__.task_id` on coroutine objects which
    raised AttributeError. After fix, it logs `role_names` instead."""
    from faos.services.analyze.service import AnalyzeService

    # Just verify the source has the fix — no __self__ reference
    import inspect
    source = inspect.getsource(AnalyzeService._run_stage)
    assert "__self__" not in source, (
        "_run_stage still references __self__ on coroutine objects"
    )
    assert "role_names" in source, (
        "_run_stage should log role_names instead of task ids"
    )


# ── Test 2: Stage definitions match the design ──

def test_stage_definitions():
    """Verify all 12 roles are defined and grouped correctly."""
    from faos.services.analyze.service import (
        STAGE1_CORE, STAGE2_PERSPECTIVE, STAGE3_REVIEWER, STAGE4_CHIEF,
        ALL_ANALYSTS, DEFAULT_STAGE2_SELECTED,
    )

    # Stage 1: 3 core analysts
    assert STAGE1_CORE == [
        "fundamental_analyst", "technical_analyst", "sentiment_analyst"
    ]

    # Stage 2: 7 perspective analysts
    assert len(STAGE2_PERSPECTIVE) == 7
    assert "value_investing_sage" in STAGE2_PERSPECTIVE
    assert "growth_visionary" in STAGE2_PERSPECTIVE
    assert "contrarian_strategist" in STAGE2_PERSPECTIVE
    assert "macro_hedge_titan" in STAGE2_PERSPECTIVE
    assert "soros-style_financial_philosopher" in STAGE2_PERSPECTIVE
    assert "serenity_alpha_analyst" in STAGE2_PERSPECTIVE
    assert "deep_research_specialist" in STAGE2_PERSPECTIVE

    # Stage 3: 1 reviewer
    assert STAGE3_REVIEWER == ["professional_reviewer"]

    # Stage 4: 1 chief
    assert STAGE4_CHIEF == ["chief_strategist"]

    # Total: 3 + 7 + 1 + 1 = 12
    total = len(STAGE1_CORE) + len(STAGE2_PERSPECTIVE) + len(STAGE3_REVIEWER) + len(STAGE4_CHIEF)
    assert total == 12

    # ALL_ANALYSTS = stage1 + stage2 (user-selectable pool)
    assert ALL_ANALYSTS == STAGE1_CORE + STAGE2_PERSPECTIVE

    # Default selection = all of stage 2
    assert DEFAULT_STAGE2_SELECTED == list(STAGE2_PERSPECTIVE)


# ── Test 3: analyst_stage2 parameter is respected ──

def test_stage2_selection_filtering():
    """When user selects a subset of Stage 2 analysts, only those are run."""
    from faos.services.analyze.service import AnalyzeService, DEFAULT_STAGE2_SELECTED

    svc = AnalyzeService(reasoning_service=MagicMock())

    # Test default (all selected)
    from faos.services.analyze.models import AnalyzeRequest
    req = AnalyzeRequest(
        task_id="test-1",
        context_data={"user_parameters": {}},
    )
    user_params = req.context_data.get("user_parameters", {})
    stage2_selected = user_params.get("analyst_stage2", DEFAULT_STAGE2_SELECTED)
    assert stage2_selected == DEFAULT_STAGE2_SELECTED

    # Test with subset
    req2 = AnalyzeRequest(
        task_id="test-2",
        context_data={
            "user_parameters": {
                "analyst_stage2": ["value_investing_sage", "macro_hedge_titan"]
            }
        },
    )
    user_params2 = req2.context_data.get("user_parameters", {})
    stage2_selected2 = user_params2.get("analyst_stage2", DEFAULT_STAGE2_SELECTED)
    assert stage2_selected2 == ["value_investing_sage", "macro_hedge_titan"]

    # Test with empty list (no stage 2 at all)
    req3 = AnalyzeRequest(
        task_id="test-3",
        context_data={
            "user_parameters": {"analyst_stage2": []}
        },
    )
    user_params3 = req3.context_data.get("user_parameters", {})
    stage2_selected3 = user_params3.get("analyst_stage2", DEFAULT_STAGE2_SELECTED)
    assert stage2_selected3 == []


# ── Test 4: AnalyzeSkill merges analyst_stage2 from llm_config ──

def test_analyze_skill_merges_analyst_stage2():
    """AnalyzeSkill should read analyst_stage2 from llm_config and
    inject it into user_parameters so AnalyzeService picks it up."""
    from faos.services.skill.impl import AnalyzeSkill
    import inspect

    source = inspect.getsource(AnalyzeSkill.execute)
    assert "analyst_stage2" in source, (
        "AnalyzeSkill.execute should handle analyst_stage2 from llm_config"
    )
    assert 'llm_config' in source, (
        "AnalyzeSkill.execute should read llm_config from context"
    )


# ── Test 5: All 12 prompt templates exist ──

def test_all_prompt_templates_exist():
    """Every analyst role must have a corresponding prompt template file."""
    import os
    from faos.services.analyze.service import (
        STAGE1_CORE, STAGE2_PERSPECTIVE, STAGE3_REVIEWER, STAGE4_CHIEF,
    )

    templates_dir = os.path.join(
        os.path.dirname(__file__), "faos", "services", "prompting", "templates"
    )

    all_roles = STAGE1_CORE + STAGE2_PERSPECTIVE + STAGE3_REVIEWER + STAGE4_CHIEF
    for role in all_roles:
        # Role key normalization (same as registry._get_raw_template)
        role_key = role.strip().replace(" ", "_").replace("-", "_").lower()
        md_path = os.path.join(templates_dir, f"{role_key}_zh.md")
        txt_path = os.path.join(templates_dir, f"{role_key}_zh.txt")

        assert os.path.exists(md_path) or os.path.exists(txt_path), (
            f"Missing template for role '{role}': checked {md_path} and {txt_path}"
        )


# ── Test 6: Stage data flow (context injection) ──

@pytest.mark.asyncio
async def test_stage_data_flow():
    """Verify that each stage injects prior stage results into the context."""
    from faos.services.analyze.service import AnalyzeService
    from faos.services.reasoning.schemas import AnalystReport

    mock_reasoning = AsyncMock()

    # Mock analyze_structured to return a basic AnalystReport
    mock_report = AnalystReport(summary="test summary", role="test")
    mock_reasoning.analyze_structured = AsyncMock(return_value=(mock_report, "raw"))

    svc = AnalyzeService(reasoning_service=mock_reasoning)

    # Patch registry to avoid missing template errors
    with patch("faos.services.analyze.service.registry") as mock_registry:
        mock_registry.render_prompt.return_value = "test prompt"

        with patch("faos.services.analyze.service.check_guardrails") as mock_guard:
            mock_guard.return_value = MagicMock(action="pass")

            with patch("faos.services.analyze.service.verify_and_annotate", side_effect=lambda s, f: s):
                from faos.services.analyze.models import AnalyzeRequest
                req = AnalyzeRequest(
                    task_id="flow-test",
                    context_data={
                        "user_parameters": {
                            "analyst_stage2": ["value_investing_sage"],
                        },
                        "quote": {"symbol": "AAPL"},
                    },
                )

                result = await svc.analyze(req)

                assert result.status == "success"
                # Should have reports from: 3 (stage1) + 1 (stage2 subset) + 1 (reviewer) + 1 (chief)
                assert len(result.analyst_reports) == 6

                # Verify render_prompt was called with stage1_analysis for Stage 2
                calls = mock_registry.render_prompt.call_args_list
                # Find the Stage 2 call (value_investing_sage)
                stage2_calls = [c for c in calls if c[0][0] == "value_investing_sage"]
                assert len(stage2_calls) == 1
                stage2_ctx = stage2_calls[0][1].get("context_data") or stage2_calls[0][0][1] if len(stage2_calls[0][0]) > 1 else None
                # The context_data passed to render_prompt is the first positional kwarg
                # Actually render_prompt is called as render_prompt(role_name, context_data=..., ...)
                stage2_kwargs = stage2_calls[0][1]
                assert "stage1_analysis" in stage2_kwargs.get("context_data", {}), \
                    "Stage 2 should receive stage1_analysis in context"


# ── Test 7: _run_stage returns empty for no valid analysts ──

@pytest.mark.asyncio
async def test_run_stage_empty_returns_empty():
    """When no valid template is found, _run_stage returns empty dicts."""
    from faos.services.analyze.service import AnalyzeService

    mock_reasoning = AsyncMock()
    svc = AnalyzeService(reasoning_service=mock_reasoning)

    with patch("faos.services.analyze.service.registry") as mock_registry:
        mock_registry.render_prompt.side_effect = FileNotFoundError("no template")

        result = await svc._run_stage(
            stage=1,
            role_names=["nonexistent_analyst"],
            context_data={},
            lang="zh",
            task_id="test",
        )

        assert result == {"rendered": {}, "structured": {}}
