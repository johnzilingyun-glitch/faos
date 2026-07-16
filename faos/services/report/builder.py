from typing import Dict, Any
from faos.services.report.models import Report, ReportSection

class ReportBuilder:
    """
    Constructs a standardized Report object from diverse Execution Context data.
    """
    
    def build(self, task_id: str, context_data: Dict[str, Any]) -> Report:
        analysis = context_data.get("analysis", {})
        decision = context_data.get("decision", {})
        
        symbol = analysis.get('symbol', 'UNKNOWN')
        
        report = Report(
            title=f"FAOS Analysis Report for {symbol}",
            summary="This report summarizes the multi-agent analysis, consensus, and final investment decision.",
            metadata={"task_id": task_id, "symbol": symbol}
        )
        
        # Section 1: Executive Summary / Market Data
        price = analysis.get('price', 0.0)
        target = analysis.get('target_price', 0.0)
        sentiment = analysis.get('sentiment', 0.0)
        
        market_section = ReportSection(
            title="Market Analysis",
            content=f"Current Price: ${price:.2f}\nTarget Price: ${target:.2f}\nNews Sentiment: {sentiment:.2f}"
        )
        report.sections.append(market_section)
        
        # Section 2: Investment Decision
        action = decision.get('action', 'UNKNOWN')
        confidence = decision.get('confidence', 0.0) * 100
        strategy = decision.get('strategy', 'N/A')
        
        decision_section = ReportSection(
            title="Investment Decision",
            content=f"**Action**: {action}\n**Confidence**: {confidence:.1f}%\n**Strategy**: {strategy}"
        )
        report.sections.append(decision_section)
        
        # Section 3: Risk & Evidence
        risk = decision.get('risk', 'N/A')
        reason = decision.get('reason', 'N/A')
        evidence_list = decision.get('evidence', [])
        
        evidence_str = "\n".join([f"- {e}" for e in evidence_list]) if evidence_list else "No explicit evidence provided."
        
        risk_section = ReportSection(
            title="Risk & Evidence",
            content=f"**Risk Level**: {risk}\n**Reason**: {reason}\n\n**Supporting Evidence**:\n{evidence_str}"
        )
        report.sections.append(risk_section)
        
        return report
