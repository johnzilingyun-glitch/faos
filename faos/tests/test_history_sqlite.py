import urllib.request
import json
import time
import sys
from faos.services.history import history_storage

def test_sqlite_direct():
    print("=== Testing SQLite Storage Direct Operations ===")
    
    # 1. Clear test DB
    history_storage.clear_all()
    print("1. Cleared SQLite database successfully.")
    
    # 2. Insert test record
    test_id = f"test_{int(time.time())}"
    test_record = {
        "id": test_id,
        "symbol": "TSLA",
        "timestamp": "2026-07-22 20:59:00",
        "chatHistory": [{"role": "user", "content": "帮我分析特斯拉"}],
        "followUpHistory": [{"role": "user", "content": "支撑位在哪"}],
        "reportContent": "# 特斯拉 TSLA 分析研报\n当前股价处于强支撑位...",
        "decision": {"pm": {"decision": "BUY", "confidence": "High", "reasoning": "技术面突破"}},
        "analysisReports": {"market": "看多", "fundamentals": "强劲"},
        "discussion": {"graph": []},
        "marketData": {"symbol": "TSLA", "prices": [220, 225, 230]}
    }
    
    saved = history_storage.save_record(test_record)
    assert saved is True, "Failed to save record to SQLite"
    print(f"2. Saved test record '{test_id}' for TSLA to SQLite.")
    
    # 3. Retrieve list
    records = history_storage.list_records()
    assert len(records) > 0, "No records returned from SQLite"
    assert records[0]["symbol"] == "TSLA", f"Expected symbol TSLA, got {records[0]['symbol']}"
    assert records[0]["decision"]["pm"]["decision"] == "BUY"
    print("3. Retrieved and verified record contents from SQLite.")
    
    # 4. Delete test record
    deleted = history_storage.delete_record(test_id)
    assert deleted is True, "Failed to delete test record"
    
    remaining = history_storage.list_records()
    assert len(remaining) == 0, "Record still exists after delete"
    print("4. Deleted record successfully from SQLite.")
    print("[SUCCESS] Direct SQLite Storage Tests Passed!\n")

def test_backend_api():
    print("=== Testing Backend REST API (http://localhost:8088/api/history) ===")
    base_url = "http://localhost:8088/api/history"
    
    test_id = f"api_test_{int(time.time())}"
    payload = {
        "id": test_id,
        "symbol": "AAPL",
        "timestamp": "2026-07-22 20:59:30",
        "chatHistory": [{"role": "user", "content": "Analyze AAPL"}],
        "followUpHistory": [],
        "reportContent": "# Apple Inc. (AAPL) Report\nBullish momentum.",
        "decision": {"pm": {"decision": "BUY", "confidence": "90%", "reasoning": "Strong quarterly earnings."}},
        "analysisReports": {},
        "discussion": {},
        "marketData": {}
    }
    
    # 1. POST /api/history
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(base_url, data=data_bytes, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as resp:
        res_json = json.loads(resp.read().decode('utf-8'))
        assert res_json.get("status") == "ok", f"POST failed: {res_json}"
    print(f"1. POST /api/history returned status: ok for record {test_id}")
    
    # 2. GET /api/history
    req_get = urllib.request.Request(base_url, method='GET')
    with urllib.request.urlopen(req_get) as resp:
        records = json.loads(resp.read().decode('utf-8'))
        assert len(records) > 0, "GET /api/history returned empty list"
        target = next((r for r in records if r["id"] == test_id), None)
        assert target is not None, f"Record {test_id} not found in GET response"
        assert target["symbol"] == "AAPL"
    print(f"2. GET /api/history verified record {test_id} exists in SQLite.")
    
    # 3. DELETE /api/history/{id}
    del_url = f"{base_url}/{test_id}"
    req_del = urllib.request.Request(del_url, method='DELETE')
    with urllib.request.urlopen(req_del) as resp:
        res_json = json.loads(resp.read().decode('utf-8'))
        assert res_json.get("status") == "ok", f"DELETE failed: {res_json}"
    print(f"3. DELETE /api/history/{test_id} returned status: ok")
    
    # 4. Verify deletion
    with urllib.request.urlopen(req_get) as resp:
        records = json.loads(resp.read().decode('utf-8'))
        target = next((r for r in records if r["id"] == test_id), None)
        assert target is None, f"Record {test_id} still present after deletion"
    print("4. Verified record deleted from backend REST API.")
    print("[SUCCESS] Backend History REST API Tests Passed!\n")

if __name__ == "__main__":
    try:
        test_sqlite_direct()
        test_backend_api()
        print(">>> ALL SQLite History Tests Passed Successfully!")
    except Exception as e:
        print(f"[ERROR] Test Failed: {e}")
        sys.exit(1)
