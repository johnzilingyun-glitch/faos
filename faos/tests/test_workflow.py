import pytest
from faos.services.workflow.models import WorkflowDefinition, WorkflowNodeDef
from faos.services.workflow.service import WorkflowService
from faos.services.workflow.standard import get_analyze_stock_workflow

def test_workflow_service_registration():
    service = WorkflowService()
    workflow = get_analyze_stock_workflow()
    
    # Register workflow
    service.register_workflow(workflow)
    
    # Verify retrieval
    retrieved = service.get_workflow("AnalyzeStockWorkflow")
    assert retrieved is not None
    assert retrieved.name == "Analyze Stock Workflow"
    assert len(retrieved.nodes) == 6
    
    # Verify non-existent
    assert service.get_workflow("NonExistent") is None

def test_standard_analyze_workflow():
    workflow = get_analyze_stock_workflow()
    assert workflow.id == "AnalyzeStockWorkflow"
    
    # Check nodes
    node_ids = [n.id for n in workflow.nodes]
    assert "node1" in node_ids
    assert "node2" in node_ids
    assert "node3" in node_ids
    assert "node_discuss" in node_ids
    assert "node_decision" in node_ids
    assert "node4" in node_ids
    
    # Check dependencies
    node3 = next(n for n in workflow.nodes if n.id == "node3")
    assert "node1" in node3.dependencies
    assert "node2" in node3.dependencies
    
    node_discuss = next(n for n in workflow.nodes if n.id == "node_discuss")
    assert "node3" in node_discuss.dependencies

    node_decision = next(n for n in workflow.nodes if n.id == "node_decision")
    assert "node_discuss" in node_decision.dependencies
    
    node4 = next(n for n in workflow.nodes if n.id == "node4")
    assert "node_decision" in node4.dependencies
