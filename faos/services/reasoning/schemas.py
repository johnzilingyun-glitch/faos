"""
Structured reasoning schemas (FAOS structured-evidence refactor, Phase 0).

These Pydantic models are the shared contract that lets agents emit
*structured* output instead of free-text essays. The core idea:

    Facts (objective)  →  Inference (subjective)  →  Confidence (explicit)

Every field has a sensible default so that:
  * mock mode can construct a valid instance with `Model()`, and
  * tolerant parsing never hard-fails on partial LLM output.

Nothing here imports from `faos.core` — this keeps the core runtime
decoupled from business schemas (Frozen Architecture).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Fact(BaseModel):
    """A single objective, verifiable data point (NOT an opinion)."""

    metric: str = Field(default="", description="Name of the metric, e.g. 'PE (TTM)'")
    value: str = Field(default="", description="Observed value as a string, e.g. '10.2'")
    peer_avg: Optional[str] = Field(default=None, description="Industry/peer average for comparison")
    hist_percentile: Optional[str] = Field(default=None, description="Historical percentile, e.g. '25%'")
    source: str = Field(default="", description="Where this fact came from (provider/filing/etc.)")


class Evidence(BaseModel):
    """A cited external evidence item (news / report / filing)."""

    id: str = Field(default="", description="Short stable id, e.g. 'E1'")
    source: str = Field(default="", description="Publisher/source, e.g. 'Reuters'")
    headline: str = Field(default="", description="Headline or claim summary")
    quantified_impact: str = Field(default="", description="Quantified impact, e.g. '全球供给 -300kt'")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Reliability 0-1")


class Signal(BaseModel):
    """A structured technical / sentiment signal (observation + reading)."""

    name: str = Field(default="", description="Signal name, e.g. 'Relative Strength vs sector'")
    observation: str = Field(default="", description="Objective observation, e.g. '连续10天跑赢板块'")
    interpretation: str = Field(default="", description="What it implies for the thesis")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class Inference(BaseModel):
    """A subjective conclusion derived FROM facts/evidence/signals."""

    statement: str = Field(default="", description="The inference / opinion")
    based_on: List[str] = Field(default_factory=list, description="metrics/ids this relies on")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AnalystReport(BaseModel):
    """
    Structured output for a single analyst.

    Cleanly separates objective Facts/Evidence/Signals from subjective
    Inferences, each carrying an explicit confidence. `summary` is a short
    synthesis that must NOT re-introduce the company.
    """

    role: str = Field(default="", description="Analyst role name")
    facts: List[Fact] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    signals: List[Signal] = Field(default_factory=list)
    inferences: List[Inference] = Field(default_factory=list)
    summary: str = Field(default="", description="One-paragraph synthesis (no company re-introduction)")

    def render(self, lang: str = "zh") -> str:
        """Render this structured report back to Markdown for back-compat
        (report builder + frontend still consume plain strings)."""
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        L = {
            "summary": "结论摘要" if zh else "Summary",
            "facts": "关键事实" if zh else "Key Facts",
            "metric": "指标" if zh else "Metric",
            "value": "数值" if zh else "Value",
            "peer": "同业均值" if zh else "Peer Avg",
            "hist": "历史分位" if zh else "Hist. %ile",
            "evidence": "证据" if zh else "Evidence",
            "signals": "信号" if zh else "Signals",
            "inferences": "推断" if zh else "Inferences",
            "conf": "置信度" if zh else "conf",
            "based": "依据" if zh else "based on",
        }
        lines: List[str] = []

        if self.summary:
            lines.append(f"**{L['summary']}**：{self.summary}\n")

        if self.facts:
            lines.append(f"**{L['facts']}**\n")
            lines.append(f"| {L['metric']} | {L['value']} | {L['peer']} | {L['hist']} |")
            lines.append("| --- | --- | --- | --- |")
            for f in self.facts:
                lines.append(
                    f"| {f.metric or '-'} | {f.value or '-'} | {f.peer_avg or '-'} | {f.hist_percentile or '-'} |"
                )
            lines.append("")

        if self.evidence:
            lines.append(f"**{L['evidence']}**\n")
            for e in self.evidence:
                tag = f"[{e.id}] " if e.id else ""
                src = f"（{e.source}" if e.source else "（"
                src += f" · {L['conf']} {e.confidence:.0%}）"
                impact = f" — {e.quantified_impact}" if e.quantified_impact else ""
                lines.append(f"- {tag}{e.headline}{src}{impact}")
            lines.append("")

        if self.signals:
            lines.append(f"**{L['signals']}**\n")
            for s in self.signals:
                interp = f" → {s.interpretation}" if s.interpretation else ""
                lines.append(f"- **{s.name}**：{s.observation}{interp}（{L['conf']} {s.confidence:.0%}）")
            lines.append("")

        if self.inferences:
            lines.append(f"**{L['inferences']}**\n")
            for i in self.inferences:
                based = f"（{L['based']}：{', '.join(i.based_on)}）" if i.based_on else ""
                lines.append(f"- {i.statement}{based}（{L['conf']} {i.confidence:.0%}）")
            lines.append("")

        return "\n".join(lines).strip()


# Compact, token-efficient schema hint injected into the prompt for structured
# output. Cheaper than dumping the full JSON Schema (which matters because
# repetition/verbosity is exactly the problem we are fixing).
ANALYST_REPORT_JSON_HINT = (
    '{\n'
    '  "facts": [{"metric": str, "value": str, "peer_avg": str|null, '
    '"hist_percentile": str|null, "source": str}],\n'
    '  "evidence": [{"id": "E1", "source": str, "headline": str, '
    '"quantified_impact": str, "confidence": 0.0-1.0}],\n'
    '  "signals": [{"name": str, "observation": str, "interpretation": str, '
    '"confidence": 0.0-1.0}],\n'
    '  "inferences": [{"statement": str, "based_on": [str], "confidence": 0.0-1.0}],\n'
    '  "summary": str\n'
    '}'
)


def build_fact_sheet(
    provider_outputs: Dict[str, Any],
    user_parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the canonical FactSheet ONCE from raw provider data (deterministic,
    NO LLM). Injected into every downstream agent so nobody re-introduces the
    company — they reference these established facts instead.
    """
    user_parameters = user_parameters or {}
    quote = provider_outputs.get("quote") or {}
    news = provider_outputs.get("news") or []

    symbol = user_parameters.get("symbol") or quote.get("symbol") or "Asset"

    fact_sheet: Dict[str, Any] = {
        "symbol": symbol,
        "name": quote.get("name") or quote.get("longName") or symbol,
    }

    # Carry through whatever quote metrics the provider gave us, without
    # assuming a fixed shape. Keep it flat and small.
    for key in (
        "price", "change", "currency", "market_cap", "marketCap",
        "pe", "peRatio", "pb", "sector", "industry", "exchange", "as_of",
    ):
        if key in quote and quote.get(key) not in (None, ""):
            fact_sheet[key] = quote.get(key)

    if isinstance(news, list) and news:
        fact_sheet["news_count"] = len(news)
        sources = []
        for item in news:
            if isinstance(item, dict):
                src = item.get("source")
                if src and src not in sources:
                    sources.append(src)
        if sources:
            fact_sheet["news_sources"] = sources[:6]

    return fact_sheet
