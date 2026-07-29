import json
import requests

payload = {
    "question": "为什么建议观望而不是买入？",
    "symbol": "AAPL",
    "report_content": "AAPL 当前价 325.89，RSI(14) 44.45 中性偏弱，MACD -0.32 短期动能偏弱。综合裁决 HOLD 观望。",
    "conversation": [
        {"role": "user", "content": "支撑位在哪"},
        {"role": "assistant", "content": "约在 315 附近"},
    ],
    "llm_config": {"provider": "mock", "language": "zh"},
}

r = requests.post("http://localhost:8088/api/report/followup", json=payload, timeout=60)
result = {"status": r.status_code, "answer": r.json().get("answer")}
with open("d:/zily/faos/_fu.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print("STATUS", r.status_code)
