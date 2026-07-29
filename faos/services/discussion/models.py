from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

class AgentOpinion(BaseModel):
    name: str = Field(..., description="Name of the agent (e.g., Fundamental Analyst)")
    role: str = Field(..., description="Role of the agent")
    opinion: str = Field(..., description="The textual opinion of the agent")
    confidence: float = Field(..., description="Confidence score from 0.0 to 1.0")
    structured: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured payload (claims / rebuttals / judgment) when available"
    )

class DiscussionRequest(BaseModel):
    task_id: str
    context_data: Dict[str, Any] = Field(default_factory=dict, description="The data to discuss")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="Dynamic LLM configuration")

class DiscussionResponse(BaseModel):
    status: str = Field(..., description="Status of the discussion, 'success' or 'failed'")
    consensus: str = Field(default="", description="The synthesized final consensus")
    opinions: List[AgentOpinion] = Field(default_factory=list, description="The individual agent opinions")
    error: str = Field(default="")


# ── Structured debate schemas (Phase 2: real debate) ──────────────────────

class Claim(BaseModel):
    """A single, numbered bull thesis point that can be attacked individually."""
    id: str = Field(default="", description="Short id like 'C1'")
    statement: str = Field(default="")
    evidence_refs: List[str] = Field(default_factory=list, description="Referenced evidence/fact ids (E1, metric names)")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class BullCase(BaseModel):
    claims: List[Claim] = Field(default_factory=list)
    summary: str = Field(default="")

    def render(self, lang: str = "zh") -> str:
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        conf = "置信度" if zh else "conf"
        ev = "依据" if zh else "evidence"
        lines: List[str] = []
        lines.append("#### 🟢 多头核心论点 (Bull Case)" if zh else "#### 🟢 Bull Case Claims")
        for c in self.claims:
            cid = f"**[{c.id}]** " if c.id else "- "
            refs = f" *(依据: {', '.join(c.evidence_refs)})*" if c.evidence_refs else ""
            lines.append(f"- {cid}{c.statement}{refs} *({conf} {c.confidence:.0%})*")

        clean_sum = self.summary.strip()
        if "{" in clean_sum or '"summary"' in clean_sum:
            import re
            m = re.search(r'"summary"\s*:\s*"([^"]+)"', clean_sum)
            clean_sum = m.group(1) if m else re.sub(r'[\{\}\[\]""]', '', clean_sum).strip()

        if clean_sum:
            lines.append("")
            lines.append(f"> 💡 **看多逻辑总结**: {clean_sum}" if zh else f"> 💡 **Bull Thesis Summary**: {clean_sum}")
        return "\n".join(lines).strip()


class Rebuttal(BaseModel):
    """A point-by-point attack targeting a specific bull claim."""
    target_claim_id: str = Field(default="", description="Which bull claim id this attacks")
    counter: str = Field(default="")
    evidence_refs: List[str] = Field(default_factory=list)
    strength: float = Field(default=0.5, ge=0.0, le=1.0, description="How damaging the rebuttal is")


class BearCase(BaseModel):
    rebuttals: List[Rebuttal] = Field(default_factory=list)
    extra_risks: List[Claim] = Field(default_factory=list, description="Bear's own risks not tied to a bull claim")
    summary: str = Field(default="")

    def render(self, lang: str = "zh") -> str:
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        strg = "杀伤力" if zh else "impact"
        attacks = "针对" if zh else "vs"
        extra = "额外隐患与风险" if zh else "Additional Risks"
        conf = "置信度" if zh else "conf"
        ev = "依据" if zh else "evidence"
        lines: List[str] = []
        lines.append("#### 🔴 空头反驳与风险 (Bear Case)" if zh else "#### 🔴 Bear Case & Counterclaims")
        for r in self.rebuttals:
            tgt = f"**[{attacks} {r.target_claim_id}]** " if r.target_claim_id else "- "
            refs = f" *(依据: {', '.join(r.evidence_refs)})*" if r.evidence_refs else ""
            lines.append(f"- {tgt}{r.counter}{refs} *({strg} {r.strength:.0%})*")
        if self.extra_risks:
            lines.append("")
            lines.append(f"**{extra}**:" if zh else f"**{extra}**:")
            for c in self.extra_risks:
                cid = f"**[{c.id}]** " if c.id else ""
                refs = f" *(依据: {', '.join(c.evidence_refs)})*" if c.evidence_refs else ""
                lines.append(f"- {cid}{c.statement}{refs} *({conf} {c.confidence:.0%})*")

        clean_sum = self.summary.strip()
        if "{" in clean_sum or '"summary"' in clean_sum:
            import re
            m = re.search(r'"summary"\s*:\s*"([^"]+)"', clean_sum)
            clean_sum = m.group(1) if m else re.sub(r'[\{\}\[\]""]', '', clean_sum).strip()

        if clean_sum:
            lines.append("")
            lines.append(f"> ⚠️ **看空逻辑总结**: {clean_sum}" if zh else f"> ⚠️ **Bear Thesis Summary**: {clean_sum}")
        return "\n".join(lines).strip()


class ClaimVerdict(BaseModel):
    claim_id: str = Field(default="")
    winner: str = Field(default="tie", description="'bull' | 'bear' | 'tie'")
    bull_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    bear_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale: str = Field(default="")


class DebateJudgment(BaseModel):
    verdicts: List[ClaimVerdict] = Field(default_factory=list)
    overall_winner: str = Field(default="tie", description="'bull' | 'bear' | 'tie'")
    overall_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    investment_plan: str = Field(default="", description="Concrete neutral synthesis / plan")

    def render(self, lang: str = "zh") -> str:
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        L = {
            "verdict": "逐条裁决" if zh else "Per-Claim Verdicts",
            "winner": "胜方" if zh else "winner",
            "overall": "总体裁决" if zh else "Overall Verdict",
            "plan": "投资共识计划" if zh else "Investment Plan",
            "claim": "论点" if zh else "claim",
        }
        win_map = {
            "bull": ("多头" if zh else "Bull"),
            "bear": ("空头" if zh else "Bear"),
            "tie": ("平局" if zh else "Tie"),
        }
        lines: List[str] = []
        if self.verdicts:
            lines.append(f"**{L['verdict']}**")
            for v in self.verdicts:
                w = win_map.get(v.winner, v.winner)
                lines.append(
                    f"- {L['claim']} {v.claim_id}: {L['winner']}={w} "
                    f"(bull {v.bull_confidence:.0%} / bear {v.bear_confidence:.0%}) — {v.rationale}"
                )
            lines.append("")
        w = win_map.get(self.overall_winner, self.overall_winner)
        lines.append(f"**{L['overall']}**：{w}（{self.overall_confidence:.0%}）")
        if self.investment_plan:
            lines.append("")
            lines.append(f"**{L['plan']}**")
            lines.append(self.investment_plan)
        return "\n".join(lines).strip()


# Compact JSON hints for structured debate output.
BULL_CASE_JSON_HINT = (
    '{\n'
    '  "claims": [{"id": "C1", "statement": str, "evidence_refs": [str], "confidence": 0.0-1.0}],\n'
    '  "summary": str\n'
    '}'
)

BEAR_CASE_JSON_HINT = (
    '{\n'
    '  "rebuttals": [{"target_claim_id": "C1", "counter": str, "evidence_refs": [str], "strength": 0.0-1.0}],\n'
    '  "extra_risks": [{"id": "R1", "statement": str, "evidence_refs": [str], "confidence": 0.0-1.0}],\n'
    '  "summary": str\n'
    '}'
)

DEBATE_JUDGMENT_JSON_HINT = (
    '{\n'
    '  "verdicts": [{"claim_id": "C1", "winner": "bull|bear|tie", '
    '"bull_confidence": 0.0-1.0, "bear_confidence": 0.0-1.0, "rationale": str}],\n'
    '  "overall_winner": "bull|bear|tie",\n'
    '  "overall_confidence": 0.0-1.0,\n'
    '  "investment_plan": str\n'
    '}'
)


class RiskGuard(BaseModel):
    """Structured CRO output: enforceable risk guardrails (Phase 3)."""
    stop_loss: str = Field(default="", description="Explicit stop-loss line/logic")
    position_sizing: str = Field(default="", description="Position limit / sizing rule")
    hedges: List[str] = Field(default_factory=list, description="Black-swan hedging actions")
    risk_level: str = Field(default="medium", description="'low' | 'medium' | 'high'")
    risk_score: int = Field(default=50, ge=0, le=100)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    notes: str = Field(default="", description="Stress-test remarks / plan corrections")

    def render(self, lang: str = "zh") -> str:
        zh = str(lang).lower() in ("zh", "chinese", "cn", "zh-cn")
        risk_map = {"low": "低" if zh else "Low", "medium": "中" if zh else "Medium", "high": "高" if zh else "High"}
        L = {
            "stop": "止损线" if zh else "Stop Loss",
            "pos": "仓位限制" if zh else "Position Sizing",
            "hedge": "黑天鹅对冲" if zh else "Black-Swan Hedges",
            "risk": "风险等级" if zh else "Risk Level",
            "conf": "置信度" if zh else "Confidence",
            "notes": "压力测试备注" if zh else "Stress-Test Notes",
        }
        lines = [
            f"- **{L['stop']}**：{self.stop_loss or '-'}",
            f"- **{L['pos']}**：{self.position_sizing or '-'}",
        ]
        if self.hedges:
            lines.append(f"- **{L['hedge']}**：")
            lines.extend(f"  - {h}" for h in self.hedges)
        lines.append(
            f"- **{L['risk']}**：{risk_map.get(self.risk_level, self.risk_level)}"
            f"（{self.risk_score}/100，{L['conf']} {self.confidence:.0%}）"
        )
        if self.notes:
            lines.append(f"- **{L['notes']}**：{self.notes}")
        return "\n".join(lines)


RISK_GUARD_JSON_HINT = (
    '{\n'
    '  "stop_loss": str,\n'
    '  "position_sizing": str,\n'
    '  "hedges": [str],\n'
    '  "risk_level": "low|medium|high",\n'
    '  "risk_score": 0-100,\n'
    '  "confidence": 0.0-1.0,\n'
    '  "notes": str\n'
    '}'
)
