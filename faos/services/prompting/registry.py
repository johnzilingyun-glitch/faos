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
            # A-stock financials are nested: quote["financials"]["summary"]
            fin_summary = {}
            if isinstance(quote.get("financials"), dict):
                fin_summary = quote["financials"].get("summary", {}) or {}
            _ALIASES = {
                # Quote aliases (a_stock_provider → yfinance)
                "pe_ttm": ("trailingPE", "pe"),
                "change_pct": ("changePercent",),
                "amount": ("totalAmount",),
                "market_cap": ("marketCap",),
                "turnover_pct": ("turnoverRate",),
                "open": ("openPrice",),
                "high": ("highPrice",),
                "low": ("lowPrice",),
                "last_close": ("previousClose",),
                # Financial summary aliases (akshare → base_prompt.jinja template keys)
                "revenue": ("totalRevenue",),
                "net_profit": ("netIncome",),
                "eps": ("trailingEps", "eps"),
                "bvps": ("bookValuePerShare",),
                "ocf_per_share": ("operatingCashflow_perShare", "operatingCashflow"),
                "ocf_to_eps_ratio": ("ocfEpsRatio",),
                "gross_margin_pct": ("grossMargins", "grossMargin"),
                "net_margin_pct": ("profitMargins", "profitMargin"),
                "roe": ("returnOnEquity",),
                "debt_ratio": ("debtAssetRatio",),
                "current_ratio": ("currentRatio",),
                "quick_ratio": ("quickRatio",),
                "revenue_yoy": ("revenueGrowth", "revenueYoY"),
                "net_profit_yoy": ("earningsGrowth", "netProfitYoY", "netProfitGrowth"),
                "debt_to_equity": ("debtToEquity", "debtRatio"),
                "inventory_turnover": ("inventoryTurnover",),
            }
            # Also merge fin_summary directly into lookup so exact key matches work
            _merged = dict(fin_summary)
            _merged.update(quote)
            for key in keys:
                # 1) Direct match in merged context
                if key in _merged and _merged[key] is not None:
                    return _merged[key]
                # 2) Check aliases (quote → template key)
                for alias_key, mapped in _ALIASES.items():
                    if key in mapped and alias_key in _merged and _merged[alias_key] is not None:
                        return _merged[alias_key]
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
            def _fallback(obj):
                if hasattr(obj, "model_dump"): return obj.model_dump()
                return str(obj)
            enrichment_text = "--- [API] ADDITIONAL CONTEXT DATA ---\n" + json.dumps(remaining_context, ensure_ascii=False, indent=2, default=_fallback)

        # A-Share snapshot (a_stock_provider fields that differ from yfinance format).
        # Inject as a heading section so the LLM sees volume/turnover/open/high/low/PE/PB
        # even when the US-centric base_prompt.jinja table would render N/A.
        a_snapshot = ""
        if quote.get("source") == "AStockDirectProvider":
            a_snapshot = (
                "--- [API] A-Share Real-Time Snapshot (腾讯财经直连) ---\n"
                f"- 股票名称: {quote.get('name', 'N/A')}\n"
                f"- 最新价: {quote.get('price', 'N/A')} 元 | 涨跌幅: {quote.get('change_pct', 'N/A')}%\n"
                f"- 今日开盘: {quote.get('open', 'N/A')} | 最高: {quote.get('high', 'N/A')} | 最低: {quote.get('low', 'N/A')} | 昨收: {quote.get('last_close', 'N/A')}\n"
                f"- 成交量: {quote.get('volume', 'N/A')} 手 | 成交额: {quote.get('amount', 'N/A')} 元\n"
                f"- PE(TTM): {quote.get('pe_ttm', 'N/A')} | PB: {quote.get('pb', 'N/A')} | 总市值: {quote.get('market_cap', 'N/A')} 元\n"
                f"- 换手率: {quote.get('turnover_pct', 'N/A')}%\n"
                f"⚠ 以上为腾讯财经/A-Share 直连实时数据。PE/PB 基于最新财报(东财口径)。所有分析师必须使用这些数值作为事实基准。\n"
            )

            # Technical indicators section
            ti = quote.get("technical_indicators") or {}
            if ti:
                ti_lines = ["--- [API] Technical Indicators (基于K线历史计算) ---"]
                if ti.get("MA5"):
                    ti_lines.append(f"- MA5: {ti.get('MA5')} | MA10: {ti.get('MA10')} | MA20: {ti.get('MA20')} | MA60: {ti.get('MA60')}")
                    if ti.get("MA_short_long"):
                        ti_lines.append(f"  → MA5 vs MA20 信号: {ti.get('MA_short_long')} ({'多头排列' if ti.get('MA_short_long') == 'golden_cross' else '死叉'})")
                if ti.get("MACD_DIF") is not None:
                    ti_lines.append(f"- MACD: DIF={ti.get('MACD_DIF')} DEA={ti.get('MACD_DEA')} HIST={ti.get('MACD_HIST')} → {ti.get('MACD_SIGNAL', 'N/A')}")
                if ti.get("RSI14") is not None:
                    ti_lines.append(f"- RSI(14): {ti.get('RSI14')} → {ti.get('RSI_SIGNAL', 'N/A')}")
                if ti.get("BB_UPPER"):
                    ti_lines.append(f"- Bollinger Bands: 上轨={ti.get('BB_UPPER')} 中轨={ti.get('BB_MID')} 下轨={ti.get('BB_LOWER')} → {ti.get('BB_SIGNAL', 'N/A')}")
                if ti.get("VOLUME_LATEST"):
                    ti_lines.append(f"- 成交量: {ti.get('VOLUME_LATEST')} (vs MA20 倍数: {ti.get('VOL_RATIO')}) → {ti.get('VOL_SIGNAL', 'N/A')}")
                for k in sorted(ti.keys()):
                    if k.startswith("Price_vs_"):
                        ti_lines.append(f"- {k}: {ti[k]}%")
                ti_lines.append("⚠ 以上技术指标由系统基于K线历史直接计算，置信度高于LLM推断。技术分析师必须使用这些数值。")
                a_snapshot += "\n".join(ti_lines) + "\n"

        # Build A-stock enriched market snapshot
        astock_market = ""
        if a_snapshot:
            # Collect K-line summary for trend context
            history = quote.get("history", [])
            if history and len(history) >= 5:
                latest = history[-5:]
                kline_text = " | ".join(
                    f"{h['time']}: {h['value']}" for h in latest
                )
            else:
                kline_text = "N/A"
            astock_market = (
                f"{a_snapshot}"
                f"- 近5日收盘价: {kline_text}\n"
                f"⚠ 情绪分析师应基于以上价格序列判断量价关系、涨跌停风险、恐慌/贪婪信号。\n\n"
            )

        # A-Share financial statement snapshot (EastMoney datacenter).
        fin_snapshot = ""
        fin_s = {}
        if isinstance(quote.get("financials"), dict):
            fin_s = quote["financials"].get("summary", {}) or {}
        if fin_s:
            flines = ["--- [API] A-Share Financial Statement Snapshot (同花顺/akshare) ---"]
            rev = fin_s.get("revenue")
            np_ = fin_s.get("net_profit")
            if rev:
                flines.append(f"- 营业总收入: {rev} | 净利润: {np_ or 'N/A'}")
            if fin_s.get("eps"):
                flines.append(f"- EPS: {fin_s.get('eps')} 元 | BVPS: {fin_s.get('bvps', 'N/A')} 元")
            ry = fin_s.get("revenue_yoy")
            ny = fin_s.get("net_profit_yoy")
            if ry is not None or ny is not None:
                flines.append(f"- 营收同比: {ry if ry is not None else 'N/A'}% | 净利润同比: {ny if ny is not None else 'N/A'}%")
            ocf_ps = fin_s.get("ocf_per_share")
            if ocf_ps:
                flines.append(f"- 每股经营现金流(OCF): {ocf_ps} 元 | OCF/EPS比: {fin_s.get('ocf_to_eps_ratio', 'N/A')}")
            # debt info
            de = fin_s.get("debt_to_equity")
            dr = fin_s.get("debt_ratio")
            if de is not None or dr is not None:
                flines.append(f"- 产权比率(D/E): {de if de is not None else 'N/A'} | 资产负债率: {dr if dr is not None else 'N/A'}%")
            gm = fin_s.get("gross_margin_pct")
            nm = fin_s.get("net_margin_pct")
            if gm is not None or nm is not None:
                flines.append(f"- 毛利率: {gm if gm is not None else 'N/A'}% | 净利率: {nm if nm is not None else 'N/A'}%")
            roe_v = fin_s.get("roe")
            if roe_v is not None:
                flines.append(f"- ROE: {roe_v}% | ROE(摊薄): {fin_s.get('roe_diluted', 'N/A')}%")
            cr = fin_s.get("current_ratio")
            qr = fin_s.get("quick_ratio")
            if cr is not None or qr is not None:
                flines.append(f"- 流动比率: {cr if cr is not None else 'N/A'} | 速动比率: {qr if qr is not None else 'N/A'}")
            itr = fin_s.get("inventory_turnover")
            rd = fin_s.get("receivable_days")
            if itr is not None or rd is not None:
                flines.append(f"- 存货周转率: {itr if itr is not None else 'N/A'} | 应收天数: {rd if rd is not None else 'N/A'}")
            flines.append("⚠ 以上为同花顺/akshare 直连最新年报数据。所有分析师必须使用这些数值作为事实基准。")
            fin_snapshot = "\n".join(flines) + "\n\n"

        enrichment_text = astock_market + fin_snapshot + enrichment_text
        
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
            # ---- Tool / Function Calling Enablement ----
            "has_search_tools": True,
            "use_native_tools": True,
            "has_enrichment": False,
            "tool_descriptions": (
                "### 可用的搜索工具 (Native Function Calling)\n"
                "- **web_search(query: str)** — 搜索互联网获取实时金融信息。"
                "包括股票新闻、财报、估值、行业分析、宏观数据等。"
                "当 API 数据缺失或 N/A 时，**必须主动调用此工具获取数据**。"
            ),
            "indicators_json": "",
            "currency_warning": "",
            "history": {},
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
