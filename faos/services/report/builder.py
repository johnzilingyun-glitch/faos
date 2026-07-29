import re
from collections import Counter
from typing import Dict, Any, List
from faos.services.report.models import Report, ReportSection

class ReportBuilder:
    """
    Constructs a standardized, dynamic Report object from diverse Execution Context data.
    """

    def _collect_report_text_blocks(self, context_data: Dict[str, Any]) -> List[str]:
        """Collect major textual blocks for repetition diagnostics."""
        blocks: List[str] = []

        analysis_reports = context_data.get("analysis_reports")
        if isinstance(analysis_reports, dict):
            for rep in analysis_reports.values():
                if isinstance(rep, str):
                    blocks.append(rep)
                elif isinstance(rep, dict):
                    if isinstance(rep.get("conclusion"), str):
                        blocks.append(rep["conclusion"])
                    if isinstance(rep.get("reasoning"), str):
                        blocks.append(rep["reasoning"])

        discussion = context_data.get("discussion")
        if isinstance(discussion, dict):
            for key in ("Investment Plan", "Risk Plan"):
                if isinstance(discussion.get(key), str):
                    blocks.append(discussion[key])
            debate = discussion.get("Investment Debate")
            if isinstance(debate, dict):
                for v in debate.values():
                    if isinstance(v, str):
                        blocks.append(v)

        decision = context_data.get("decision")
        if isinstance(decision, dict):
            reason = decision.get("reason") or decision.get("pm", {}).get("reasoning")
            if isinstance(reason, str):
                blocks.append(reason)

        return [b for b in blocks if b and isinstance(b, str)]

    def _compute_repetition_diagnostics(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute lightweight repetition metrics from report source blocks.
        Sentence-level duplicate ratio = duplicated sentence instances / total sentences.
        """
        blocks = self._collect_report_text_blocks(context_data)
        if not blocks:
            return {
                "total_sentences": 0,
                "duplicate_instances": 0,
                "duplicate_ratio": 0.0,
                "top_repeated_sentences": [],
            }

        raw_text = "\n".join(blocks)
        # Split by Chinese/English sentence delimiters and line breaks.
        parts = re.split(r"[\n\r\.\!\?。！？]+", raw_text)
        normalized: List[str] = []
        for p in parts:
            s = re.sub(r"\s+", " ", p.strip().lower())
            # Keep practical Chinese/English short clauses:
            # - Chinese often has meaningful 6+ char sentences.
            # - English retains 3+ words to avoid noise.
            if not s:
                continue
            is_chinese_like = re.search(r"[\u4e00-\u9fff]", s) is not None
            if (is_chinese_like and len(s) >= 6) or (not is_chinese_like and len(s.split()) >= 3):
                normalized.append(s)

        if not normalized:
            return {
                "total_sentences": 0,
                "duplicate_instances": 0,
                "duplicate_ratio": 0.0,
                "top_repeated_sentences": [],
            }

        cnt = Counter(normalized)
        duplicate_instances = sum(c - 1 for c in cnt.values() if c > 1)
        duplicate_ratio = duplicate_instances / len(normalized)
        top = [
            {"sentence": s[:180], "count": c}
            for s, c in cnt.most_common()
            if c > 1
        ][:5]

        return {
            "total_sentences": len(normalized),
            "duplicate_instances": duplicate_instances,
            "duplicate_ratio": duplicate_ratio,
            "top_repeated_sentences": top,
        }
    
    def build(self, task_id: str, context_data: Dict[str, Any]) -> Report:
        user_params = context_data.get("user_parameters", {})
        provider_outputs = context_data.get("provider_outputs", {})
        
        # Extract symbol
        symbol = (
            user_params.get("symbol")
            or provider_outputs.get("quote", {}).get("symbol")
            or "Asset"
        )
        
        lang = str(user_params.get("language") or "zh").lower()
        is_chinese = lang in ("zh", "chinese", "cn", "zh-cn")

        if is_chinese:
            title = f"FAOS 智能金融分析报告: {symbol}"
            summary = f"基于实时行情数据、焦点新闻及 AI 多智能体团队共识汇总的 {symbol} 综合金融研报。"
            sec_titles = {
                "market": "标的概览",
                "news": "实时新闻与焦点归因",
                "analysts": "多维分析师报告",
                "debate": "多智能体辩论与共识",
                "verdict": "最终裁决与执行策略",
                "evidence": "证据链图谱"
            }
        else:
            title = f"FAOS Financial Intelligence Report: {symbol}"
            summary = f"Comprehensive intelligence report compiling market data, real-time news, and AI agent analytical consensus for {symbol}."
            sec_titles = {
                "market": "Snapshot",
                "news": "Real-Time News & Catalyst Attribution",
                "analysts": "Multi-Dimensional Analyst Insights",
                "debate": "Multi-Agent Debate & Consensus",
                "verdict": "Final Verdict & Executive Decision",
                "evidence": "Evidence Graph"
            }
        
        report = Report(
            title=title,
            summary=summary,
            metadata={"task_id": task_id, "symbol": symbol}
        )

        repetition_diag = self._compute_repetition_diagnostics(context_data)
        
        # 1. Snapshot / FactSheet — the single canonical company-info block.
        fact_sheet = context_data.get("fact_sheet") or {}
        quote = provider_outputs.get("quote")
        if fact_sheet or (quote and isinstance(quote, dict)):
            q = quote if isinstance(quote, dict) else {}
            price = fact_sheet.get("price", q.get("price", 0.0)) or 0.0
            change = fact_sheet.get("change", q.get("change", 0.0)) or 0.0
            name = fact_sheet.get("name")
            sector = fact_sheet.get("sector") or fact_sheet.get("industry")
            currency = fact_sheet.get("currency") or ""
            news_count = fact_sheet.get("news_count")
            try:
                price_str = f"{float(price):.2f}"
            except (TypeError, ValueError):
                price_str = str(price)
            chg = f" ({change:+.2f}%)" if isinstance(change, (int, float)) and change else ""
            if is_chinese:
                lines = ["**标的**: `" + str(symbol) + "`" + (f" · {name}" if name and name != symbol else "")]
                lines.append((f"**最新价**: {price_str} {currency}").rstrip() + chg)
                if sector: lines.append(f"**板块**: {sector}")
                if news_count: lines.append(f"**覆盖新闻**: {news_count} 条")
            else:
                lines = ["**Symbol**: `" + str(symbol) + "`" + (f" · {name}" if name and name != symbol else "")]
                lines.append((f"**Price**: {price_str} {currency}").rstrip() + chg)
                if sector: lines.append(f"**Sector**: {sector}")
                if news_count: lines.append(f"**News covered**: {news_count}")
            report.sections.append(ReportSection(title=sec_titles["market"], content="\n".join(lines)))

        # 2. Real-Time News & Event Attribution (if news exists)
        news = provider_outputs.get("news")
        if news:
            news_lines = []
            if isinstance(news, list):
                for idx, item in enumerate(news[:6], 1):
                    if isinstance(item, dict):
                        t = item.get("title", "Untitled")
                        s = item.get("snippet", "")
                        u = item.get("url", "")
                        src = item.get("source", "")
                        link_str = f"[{t}]({u})" if u else f"**{t}**"
                        source_label = "来源" if is_chinese else "Source"
                        summary_label = "摘要" if is_chinese else "Summary"
                        news_lines.append(f"### {idx}. {link_str}\n- **{source_label}**: {src}\n- **{summary_label}**: {s}\n")
                    elif isinstance(item, str):
                        news_lines.append(f"- {item}")
            elif isinstance(news, str):
                news_lines.append(news)
                
            if news_lines:
                report.sections.append(ReportSection(
                    title=sec_titles["news"],
                    content="\n".join(news_lines)
                ))

        # 3. Multi-Dimensional Analyst Reports (if analysis_reports exist)
        analysis_reports = context_data.get("analysis_reports")
        if analysis_reports and isinstance(analysis_reports, dict):
            reports_lines = []
            for role, rep in analysis_reports.items():
                reports_lines.append(f"### {role}")
                if isinstance(rep, dict):
                    if "conclusion" in rep:
                        conc_label = "核心结论" if is_chinese else "Conclusion"
                        reports_lines.append(f"**{conc_label}**: {rep['conclusion']}\n")
                    if "reasoning" in rep:
                        reports_lines.append(f"{rep['reasoning']}\n")
                elif isinstance(rep, str):
                    reports_lines.append(f"{rep}\n")
            if reports_lines:
                report.sections.append(ReportSection(
                    title=sec_titles["analysts"],
                    content="\n".join(reports_lines)
                ))

        # 4. Multi-Agent Discussion & Consensus (if discussion exists)
        discussion = context_data.get("discussion")
        if discussion and isinstance(discussion, dict):
            disc_lines = []
            if "Investment Debate" in discussion:
                deb = discussion["Investment Debate"]
                if isinstance(deb, dict):
                    bull_text = deb.get("Bull", "")
                    bear_text = deb.get("Bear", "")
                    if bull_text:
                        disc_lines.append(f"{bull_text}\n")
                    if bear_text:
                        disc_lines.append(f"{bear_text}\n")
            if "Investment Plan" in discussion:
                mgr_lbl = "### 👔 研究主管方案共识" if is_chinese else "### 👔 Research Manager Plan"
                disc_lines.append(f"{mgr_lbl}\n{discussion['Investment Plan']}\n")
            if "Risk Plan" in discussion:
                risk_lbl = "### 🛡️ 首席风控官防线评估" if is_chinese else "### 🛡️ Chief Risk Officer Assessment"
                disc_lines.append(f"{risk_lbl}\n{discussion['Risk Plan']}\n")
                
            if disc_lines:
                report.sections.append(ReportSection(
                    title=sec_titles["debate"],
                    content="\n".join(disc_lines)
                ))

        # 5. Investment Strategy & Verdict (if decision exists)
        decision = context_data.get("decision")
        if decision and isinstance(decision, dict):
            dec_lines = []
            action = decision.get("action") or decision.get("pm", {}).get("decision") or "NEUTRAL"
            conf = decision.get("confidence") or decision.get("pm", {}).get("confidence") or "N/A"
            reason = decision.get("reason") or decision.get("pm", {}).get("reasoning") or ""

            # Scorecard-first: render the decision card before any prose.
            scorecard = decision.get("scorecard")
            if scorecard and isinstance(scorecard, dict):
                try:
                    from faos.services.decision.models import Scorecard
                    card_md = Scorecard(**scorecard).render("zh" if is_chinese else "en")
                    dec_lines.append(card_md + "\n")
                except Exception:
                    pass
            
            act_lbl = "操作指令" if is_chinese else "Action"
            conf_lbl = "置信度评分" if is_chinese else "Confidence"
            reason_lbl = "基金经理决策理由" if is_chinese else "Manager Rationale"
            
            dec_lines.append(f"**{act_lbl}**: `{action}`\n**{conf_lbl}**: `{conf}`\n")
            if reason:
                dec_lines.append(f"**{reason_lbl}**:\n{reason}\n")
                
            trader = decision.get("trader") or decision.get("strategy")
            if trader and isinstance(trader, dict):
                strat_lbl = "#### 交易员具体执行策略" if is_chinese else "#### Execution Strategy"
                dec_lines.append(strat_lbl)
                dec_lines.append(f"- **{'交易方向' if is_chinese else 'Trade Type'}**: {trader.get('trade_type', 'N/A')}")
                dec_lines.append(f"- **{'建仓/目标价' if is_chinese else 'Entry Target'}**: {trader.get('entry_target', 'N/A')}")
                dec_lines.append(f"- **{'止损价位' if is_chinese else 'Stop Loss'}**: {trader.get('stop_loss', 'N/A')}")
                dec_lines.append(f"- **{'仓位比例' if is_chinese else 'Position Sizing'}**: {trader.get('position_sizing', 'N/A')}")

            report.sections.append(ReportSection(
                title=sec_titles["verdict"],
                content="\n".join(dec_lines)
            ))
            
        # 6. Evidence Graph appendix (Fact -> Inference -> Claim -> Decision chain)
        evidence_graph = context_data.get("evidence_graph") or {}
        if isinstance(evidence_graph, dict) and any(
            evidence_graph.get(k) for k in ("facts", "evidence", "signals", "inferences", "claims")
        ):
            facts = evidence_graph.get("facts", []) or []
            evs = evidence_graph.get("evidence", []) or []
            sigs = evidence_graph.get("signals", []) or []
            infs = evidence_graph.get("inferences", []) or []
            claims = evidence_graph.get("claims", []) or []

            def _by(node):
                b = node.get("by")
                return f" _({b})_" if b else ""

            eg_lines = []
            if is_chinese:
                eg_lines.append(
                    f"**证据节点统计**：事实 {len(facts)} · 外部证据 {len(evs)} · 信号 {len(sigs)} · 推断 {len(infs)} · 辩论论点 {len(claims)}\n"
                )
            else:
                eg_lines.append(
                    f"**Node counts**: facts {len(facts)} · evidence {len(evs)} · signals {len(sigs)} · inferences {len(infs)} · claims {len(claims)}\n"
                )
            if facts:
                eg_lines.append("**Fact**")
                for f in facts[:5]:
                    eg_lines.append(f"- {f.get('metric', '-')}: {f.get('value', '-')}{_by(f)}")
            if infs:
                eg_lines.append("\n**Inference**")
                for i in infs[:4]:
                    c = i.get("confidence")
                    cs = f"（{c:.0%}）" if isinstance(c, (int, float)) else ""
                    eg_lines.append(f"- {i.get('statement', '')}{cs}{_by(i)}")
            if claims:
                eg_lines.append("\n**Debate**")
                for c in claims[:4]:
                    txt = c.get("statement") or c.get("counter") or ""
                    eg_lines.append(f"- {txt}{_by(c)}")
            decision = context_data.get("decision")
            if isinstance(decision, dict) and decision.get("action"):
                sc = decision.get("scorecard") or {}
                rec = sc.get("recommendation")
                tail = f" · {rec}" if rec else ""
                label = "决策" if is_chinese else "Decision"
                eg_lines.append(f"\n**{label}**: `{decision.get('action')}`{tail}")

            # Repetition diagnostics: quantifiable anti-duplication KPI for report quality.
            ratio = repetition_diag.get("duplicate_ratio", 0.0)
            total = repetition_diag.get("total_sentences", 0)
            dup = repetition_diag.get("duplicate_instances", 0)
            if is_chinese:
                eg_lines.append(
                    f"\n**重复度诊断**：重复句占比 `{ratio:.1%}` （重复实例 {dup} / 句子总数 {total}）"
                )
            else:
                eg_lines.append(
                    f"\n**Repetition Diagnostics**: duplicate-sentence ratio `{ratio:.1%}` (duplicates {dup} / total sentences {total})"
                )
            top_repeated = repetition_diag.get("top_repeated_sentences", [])
            if top_repeated:
                top_label = "高频重复句" if is_chinese else "Top Repeated Sentences"
                eg_lines.append(f"- **{top_label}**:")
                for item in top_repeated:
                    eg_lines.append(f"  - ({item['count']}x) {item['sentence']}")
            report.sections.append(ReportSection(title=sec_titles["evidence"], content="\n".join(eg_lines)))
        elif repetition_diag.get("total_sentences", 0) > 0:
            # Even without evidence_graph, expose repetition diagnostics for QA.
            ratio = repetition_diag.get("duplicate_ratio", 0.0)
            total = repetition_diag.get("total_sentences", 0)
            dup = repetition_diag.get("duplicate_instances", 0)
            diag_title = sec_titles["evidence"]
            if is_chinese:
                diag_lines = [
                    f"**重复度诊断**：重复句占比 `{ratio:.1%}` （重复实例 {dup} / 句子总数 {total}）"
                ]
            else:
                diag_lines = [
                    f"**Repetition Diagnostics**: duplicate-sentence ratio `{ratio:.1%}` (duplicates {dup} / total sentences {total})"
                ]
            top_repeated = repetition_diag.get("top_repeated_sentences", [])
            if top_repeated:
                top_label = "高频重复句" if is_chinese else "Top Repeated Sentences"
                diag_lines.append(f"- **{top_label}**:")
                for item in top_repeated:
                    diag_lines.append(f"  - ({item['count']}x) {item['sentence']}")
            report.sections.append(ReportSection(title=diag_title, content="\n".join(diag_lines)))

        # Fallback if no specific section was added
        if not report.sections:
            report.sections.append(ReportSection(
                title="Analysis Summary",
                content=f"Report compiled for {symbol} based on user intent."
            ))
            
        return report
