from typing import Dict, Any
from faos.services.report.models import Report, ReportSection

class ReportBuilder:
    """
    Constructs a standardized, dynamic Report object from diverse Execution Context data.
    """
    
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
                "market": "行情概览",
                "news": "实时新闻与焦点归因",
                "analysts": "多维分析师报告",
                "debate": "多智能体辩论与共识",
                "verdict": "最终裁决与执行策略"
            }
        else:
            title = f"FAOS Financial Intelligence Report: {symbol}"
            summary = f"Comprehensive intelligence report compiling market data, real-time news, and AI agent analytical consensus for {symbol}."
            sec_titles = {
                "market": "Market Overview",
                "news": "Real-Time News & Catalyst Attribution",
                "analysts": "Multi-Dimensional Analyst Insights",
                "debate": "Multi-Agent Debate & Consensus",
                "verdict": "Final Verdict & Executive Decision"
            }
        
        report = Report(
            title=title,
            summary=summary,
            metadata={"task_id": task_id, "symbol": symbol}
        )
        
        # 1. Market Data Overview (if quote exists)
        quote = provider_outputs.get("quote")
        if quote and isinstance(quote, dict):
            price = quote.get("price", 0.0)
            change = quote.get("change", 0.0)
            if is_chinese:
                sec_content = f"**标的代码**: `{symbol}`\n**当前最新价**: ${price:.2f}"
            else:
                sec_content = f"**Symbol**: `{symbol}`\n**Current Price**: ${price:.2f}"
            if change != 0.0:
                sec_content += f" ({change:+.2f}%)"
            report.sections.append(ReportSection(title=sec_titles["market"], content=sec_content))

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
                    bull_lbl = "多头看多观点" if is_chinese else "Bull Case"
                    bear_lbl = "空头看空观点" if is_chinese else "Bear Case"
                    if "Bull" in deb: disc_lines.append(f"**{bull_lbl}**: {deb['Bull']}\n")
                    if "Bear" in deb: disc_lines.append(f"**{bear_lbl}**: {deb['Bear']}\n")
            if "Investment Plan" in discussion:
                mgr_lbl = "研究主管方案共识" if is_chinese else "Research Manager Plan"
                disc_lines.append(f"**{mgr_lbl}**: {discussion['Investment Plan']}\n")
            if "Risk Plan" in discussion:
                risk_lbl = "首席风控官防线评估" if is_chinese else "Chief Risk Officer Assessment"
                disc_lines.append(f"**{risk_lbl}**: {discussion['Risk Plan']}\n")
                
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
            
        # Fallback if no specific section was added
        if not report.sections:
            report.sections.append(ReportSection(
                title="Analysis Summary",
                content=f"Report compiled for {symbol} based on user intent."
            ))
            
        return report
