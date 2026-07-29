import pytest
from faos.execution.market_detector import detect_market
from faos.execution.planner import PlannerPipeline
from faos.core.event_bus import EventBus
from faos.services.workflow.service import WorkflowService

def test_market_detector():
    """Verify market resolution follows ALSA rules."""
    assert detect_market("AAPL") == "US-Share"
    assert detect_market("^DJI") == "US-Share"
    assert detect_market("00700.HK") == "HK-Share"
    assert detect_market("9888.hk") == "HK-Share"
    assert detect_market("600519.SS") == "A-Share"
    assert detect_market("300750.SZ") == "A-Share"
    assert detect_market("000001") == "A-Share"  # 6 digits
    assert detect_market("3690") == "HK-Share"   # 4 digits

@pytest.mark.asyncio
async def test_dynamic_planner_generation():
    """Verify Planner builds dynamic DAG and injects correct market focus."""
    event_bus = EventBus()
    workflow_service = WorkflowService()
    
    planner = PlannerPipeline(
        event_bus=event_bus,
        workflow_service=workflow_service,
        reasoning_service=None
    )
    
    # 1. Test US Stock
    us_nodes = planner._build_dynamic_stock_plan({"symbol": "NVDA"})
    
    us_node_analyze = next(n for n in us_nodes if n.id == "node3")
    assert us_node_analyze.parameters["market"] == "US-Share"
    assert "Fed rates" in us_node_analyze.parameters["market_focus"] or "企业盈利" in us_node_analyze.parameters["market_focus"]

    # 2. Test A-Share
    cn_nodes = planner._build_dynamic_stock_plan({"symbol": "600519.SS"})
    cn_node_analyze = next(n for n in cn_nodes if n.id == "node3")
    assert cn_node_analyze.parameters["market"] == "A-Share"
    assert "国内宏观" in cn_node_analyze.parameters["market_focus"]

    # 3. Test DAG parallel structure
    # node1 (fetch_data) and node2 (fetch_news) should have no dependencies
    fetch_data = next(n for n in cn_nodes if n.id == "node1")
    fetch_news = next(n for n in cn_nodes if n.id == "node2")
    assert not fetch_data.dependencies
    assert not fetch_news.dependencies
    
    # analyze (node3) should depend on both
    assert "node1" in cn_node_analyze.dependencies
    assert "node2" in cn_node_analyze.dependencies
