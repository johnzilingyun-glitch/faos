import pytest
from faos.services.memory import MemoryService, memory_service


@pytest.fixture
def memory_svc(tmp_path):
    # Fresh DB per test (pytest tmp_path) — a shared/leftover db file
    # accumulates rows across runs and breaks count-based assertions.
    yield MemoryService(db_path=str(tmp_path / "test_memory.db"))

def test_store_and_recall(memory_svc):
    symbol = "TEST_STOCK"
    role = "Fundamental Analyst"
    
    # Store a memory
    memory_svc.store(symbol, role, "This is a great stock based on PE.", confidence=0.8)
    memory_svc.store(symbol, role, "Re-evaluated, not so great anymore.", confidence=0.4)
    
    # Recall
    res = memory_svc.recall(symbol, role, limit=5)
    assert len(res.entries) == 2
    
    # Ordered by latest
    assert "not so great" in res.entries[0].analysis_summary
    assert res.entries[0].confidence == 0.4
    
    assert "great stock based on PE" in res.entries[1].analysis_summary
    
def test_recall_empty(memory_svc):
    res = memory_svc.recall("UNKNOWN", "Any Analyst")
    assert len(res.entries) == 0
    assert "无历史记忆" in res.summary
