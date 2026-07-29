import os
import json
from typing import Dict, Optional, Any
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class PromptRegistry:
    """
    Dynamically loads Markdown/TXT prompt templates from disk.
    Allows easy extension of agent personas without changing code.
    """
    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir is None:
            # Default to the templates directory alongside this file
            current_dir = os.path.dirname(__file__)
            self.templates_dir = os.path.join(current_dir, "templates")
        else:
            self.templates_dir = templates_dir
            
        self._cache: Dict[str, str] = {}
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.info(f"PromptRegistry initialized with templates dir: {self.templates_dir}")

    def render_prompt(
        self, 
        role: str, 
        context_data: Dict[str, Any], 
        language: str = "zh-CN", 
        json_hint: Optional[str] = None
    ) -> str:
        """
        Loads the role template and renders it inside base_prompt.jinja 
        using context_data (e.g. macro_data, fact_sheet).
        """
        lang_suffix = "zh" if language.lower() in ("zh-cn", "zh", "chinese") else "en"
        role_key = role.strip().replace(" ", "_").replace("-", "_").lower()
        
        # Load the role-specific markdown template
        role_template_content = self._get_raw_template(role_key, lang_suffix)
        if json_hint:
            role_template_content += f"\n\nCRITICAL: You MUST output in the following JSON format ONLY:\n```json\n{json_hint}\n```\n"

        # Prepare Jinja variables based on FAOS context
        user_params = context_data.get("user_parameters", {})
        macro_data = context_data.get("macro_data", {})
        fact_sheet = context_data.get("fact_sheet", {})
        
        # Helper function for base_prompt.jinja to fetch values from various dictionaries
        def get_val(*keys, default="N/A"):
            quote = context_data.get("quote", {})
            financials = context_data.get("financials", {})
            for key in keys:
                if key in quote and quote[key] is not None:
                    return quote[key]
                if key in financials and financials[key] is not None:
                    return financials[key]
            return default

        def fmt_num(val):
            if val is None or val == "N/A": return "N/A"
            try: return f"{float(val):,.2f}"
            except: return str(val)
            
        quote = context_data.get("quote", {})
        
        # Everything else in context_data (news, competitors, etc.) goes to enrichment_text
        remaining_context = {
            k: v for k, v in context_data.items() 
            if k not in ["quote", "financials", "macro_data", "fact_sheet", "user_parameters", "stock_data", "current_date"]
        }
        enrichment_text = ""
        if remaining_context:
            enrichment_text = "--- [API] ADDITIONAL CONTEXT DATA ---\n" + json.dumps(remaining_context, ensure_ascii=False, indent=2)
        
        render_vars = {
            "role": role,
            "template": role_template_content,
            "is_zh": lang_suffix == "zh",
            "is_sector_intermediate": False,
            "is_markdown_intermediate": False,
            "is_final_round": True if user_params.get("is_final") else False,
            "macro_data": macro_data,
            "stock_data": context_data,
            "fact_sheet_json": json.dumps(fact_sheet, ensure_ascii=False, indent=2) if fact_sheet else "",
            "enrichment_text": enrichment_text,
            "get_val": get_val,
            "fmt_num": fmt_num,
            "symbol": user_params.get("symbol", "UNKNOWN"),
            "name": quote.get("longName") or quote.get("shortName") or "UNKNOWN",
            "current_date": context_data.get("current_date", "Today"),
            "long_name": quote.get("longName", "UNKNOWN"),
            "full_code": quote.get("symbol", "UNKNOWN"),
            "exchange_display": quote.get("exchange", "UNKNOWN"),
            "industry": quote.get("industry", "UNKNOWN"),
            "sector": quote.get("sector", "N/A"),
            "listing_date": "N/A",
            "biz_summary": quote.get("longBusinessSummary", ""),
            "market": "US" if quote.get("exchange", "").upper() in ("NYQ", "NMS", "NASDAQ", "NYSE") else "A-Share",
            "listing_currency": quote.get("currency", "USD"),
            "currency_note": "",
            "fin_currency": quote.get("financialCurrency", "USD"),
            
            # Default empty variables to prevent Jinja UndefinedError when calling .get()
            "brain_ctx": {},
            "macro_indicators": {},
            "macro_regime_text": "",
            "peer_data": {},
            "sentiment_data": {},
            "top_circulating_holders": [],
            "audit_data": {},
            "intraday_volume": {},
            "quarterly_history": [],
            "valuation_guidance": "",
            "data_quality": {},
            "dividend_history": [],
            "buyback": {},
            "coal_price": {},
            "commodity_data": {},
            "cross_listing": {},
            "sector_stocks": [],
        }
        
        # Render the base_prompt
        try:
            base_template = self.jinja_env.get_template("base_prompt.jinja")
            return base_template.render(**render_vars)
        except Exception as e:
            logger.error(f"Failed to render base_prompt.jinja: {e}")
            # Fallback to just returning the role template + fact sheet if jinja fails
            return f"Role: {role}\n\nFact Sheet:\n{render_vars['fact_sheet_json']}\n\n{role_template_content}"

    def _get_raw_template(self, role_key: str, lang_suffix: str) -> str:
        # Prefer markdown over txt if both exist
        for ext in ["md", "txt"]:
            filename = f"{role_key}_{lang_suffix}.{ext}"
            path = os.path.join(self.templates_dir, filename)
            
            if path in self._cache:
                return self._cache[path]
                
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    template = f.read()
                    self._cache[path] = template
                    return template
                    
        # Fallback to English if ZH not found
        if lang_suffix == "zh":
            logger.warning(f"Template for {role_key} (zh) not found. Falling back to English.")
            return self._get_raw_template(role_key, "en")
            
        raise FileNotFoundError(f"Template not found for role '{role_key}' in {self.templates_dir}")

# Global registry instance
registry = PromptRegistry()
