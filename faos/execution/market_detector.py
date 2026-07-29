def detect_market(symbol: str) -> str:
    """
    归一化市场判定。
    根据代码后缀或长度判定股票所属市场 (A-Share, HK-Share, US-Share)。
    
    规则：
    - .SH, .SS, .SZ: A-Share
    - .HK: HK-Share
    - 无后缀纯字母 / 带 ^: US-Share
    - 6位纯数字: A-Share
    - 4~5位纯数字: HK-Share
    """
    s = (symbol or "").strip().upper()
    if not s:
        return "Unknown"
        
    if s.endswith((".SH", ".SS", ".SZ")):
        return "A-Share"
        
    if s.endswith(".HK"):
        return "HK-Share"
        
    if s.startswith("^") or s.isalpha():
        return "US-Share"
        
    # 纯数字判断
    digits = s.replace(".", "").replace("-", "")
    if digits.isdigit():
        if len(digits) == 6:
            return "A-Share"
        if 4 <= len(digits) <= 5:
            return "HK-Share"
            
    # 默认美股
    return "US-Share"
