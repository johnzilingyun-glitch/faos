import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Patterns that match common financial figure mentions in Chinese/English
NUMERIC_PATTERNS = [
    # Chinese
    (r'(?:PE|市盈率|P/E)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(倍|x|X)?', 'pe'),
    (r'(?:PB|市净率|P/B)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(倍|x|X)?', 'pb'),
    (r'(?:ROE|净资产收益率)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(%)?', 'roe'),
    (r'(?:总营收|营业总收入|营业收入)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(亿|万|百万|B|M|K)?', 'revenue'),
    (r'(?:净利润|归母净利润|扣非净利润)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(亿|万|百万|B|M|K)?', 'net_income'),
    (r'(?:市值|总市值)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(亿|万|百万|B|M|K)?', 'market_cap'),
    (r'(?:股息率|分红率)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(%)?', 'dividend_yield'),
    (r'(?:毛利率)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)\s*(%)?', 'gross_margin'),
    (r'(?:EPS|每股收益)[\s:：=是为约达到在]{0,5}\s*(\d+\.?\d*)()?', 'eps'),
    # English
    (r'(?:PE|P/E)\s*(?:ratio)?[\s:=]{0,3}\s*(\d+\.?\d*)()?', 'pe'),
    (r'(?:PB|P/B)\s*(?:ratio)?[\s:=]{0,3}\s*(\d+\.?\d*)()?', 'pb'),
    (r'ROE[\s:=]{0,3}\s*(\d+\.?\d*)\s*(%)?', 'roe'),
    (r'(?:revenue|Revenue)[\s:=]{0,3}\s*(\d+\.?\d*)\s*(B|M|bn|mn)?', 'revenue'),
    (r'(?:market cap|Market Cap|marketcap)[\s:=]{0,3}\s*(\d+\.?\d*)\s*(B|T|M|bn|tn)?', 'market_cap'),
]

UNIT_MULTIPLIERS = {
    '亿': 1e8, '万': 1e4, '百万': 1e6,
    'B': 1e9, 'M': 1e6, 'K': 1e3,
    'bn': 1e9, 'mn': 1e6,
    'T': 1e12, 'tn': 1e12,
}

PERCENT_FIELDS = {'roe', 'dividend_yield', 'gross_margin'}
DEFAULT_TOLERANCE = 0.05

def normalize_value(raw_val: float, unit: str, field: str) -> float:
    val = raw_val
    if unit in UNIT_MULTIPLIERS:
        val *= UNIT_MULTIPLIERS[unit]
    
    # If the text says "ROE 15%", the raw_val is 15. The fact_sheet stores 0.15.
    if field in PERCENT_FIELDS and unit == '%':
        val /= 100.0
    elif field in PERCENT_FIELDS and raw_val > 1.0 and unit == '':
        # Heuristic: "ROE is 15" meaning 15%
        val /= 100.0
        
    return val

def _find_fact_value(field: str, facts: Dict[str, Any]) -> float:
    """Find the numerical value for the field in the facts dictionary (recursive)."""
    # FactSheet has sections like "metrics", "financials", etc.
    # Simple recursive search
    def search(d):
        if not isinstance(d, dict):
            return None
        if field in d and isinstance(d[field], (int, float)):
            return float(d[field])
        # Sometimes keys are capitalized or different
        for k, v in d.items():
            if k.lower() == field or (field == "net_income" and k.lower() in ("netincome", "net_income")):
                if isinstance(v, (int, float)):
                    return float(v)
            if isinstance(v, dict):
                res = search(v)
                if res is not None:
                    return res
        return None
    return search(facts)

def verify_and_annotate(text: str, facts: Dict[str, Any]) -> str:
    """
    Parses LLM generated text for financial numbers.
    If a number drastically contradicts the `facts`, appends a Markdown warning tag.
    Returns the annotated text.
    """
    if not text or not facts:
        return text

    annotated_text = text
    # We do replacements from end to start to not mess up indices
    replacements = []

    for pattern, field in NUMERIC_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw_str = match.group(1)
            unit_str = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
            
            try:
                raw_val = float(raw_str)
            except ValueError:
                continue
                
            norm_val = normalize_value(raw_val, unit_str, field)
            fact_val = _find_fact_value(field, facts)
            
            if fact_val is not None and fact_val != 0:
                # Calculate relative error
                error = abs((norm_val - fact_val) / fact_val)
                if error > DEFAULT_TOLERANCE:
                    # Hallucination detected
                    logger.warning(f"Grounding failed for {field}: LLM said {norm_val}, Fact is {fact_val}")
                    
                    # We will append a warning right after the match
                    end_idx = match.end()
                    # Format the fact nicely
                    display_fact = fact_val
                    if field in PERCENT_FIELDS:
                        display_fact = f"{fact_val * 100:.2f}%"
                    elif abs(fact_val) >= 1e8:
                        display_fact = f"{fact_val / 1e8:.2f}亿"
                    else:
                        display_fact = f"{fact_val:.2f}"
                        
                    warning_tag = f" <mark>⚠️ 数据查证不符，底层真实 {field.upper()} 为 {display_fact}</mark> "
                    replacements.append((end_idx, warning_tag))
    
    # Sort replacements descending by index
    replacements.sort(key=lambda x: x[0], reverse=True)
    
    for idx, tag in replacements:
        annotated_text = annotated_text[:idx] + tag + annotated_text[idx:]
        
    return annotated_text
