from faos.services.workflow.models import WorkflowDefinition, WorkflowNodeDef

def get_analyze_stock_workflow() -> WorkflowDefinition:
    """
    Standard Workflow for Analyzing a Stock.
    Composes FetchData, FetchNews, Analyze, and GenerateReport capabilities into a DAG.
    """
    return WorkflowDefinition(
        id="AnalyzeStockWorkflow",
        name="Analyze Stock Workflow",
        description="Standard workflow to analyze a stock and generate a report",
        nodes=[
            WorkflowNodeDef(id="node1", capability="FetchData"),
            WorkflowNodeDef(id="node2", capability="FetchNews"),
            WorkflowNodeDef(
                id="node3", 
                capability="Analyze", 
                dependencies=["node1", "node2"]
            ),
            WorkflowNodeDef(
                id="node4", 
                capability="GenerateReport", 
                dependencies=["node3"]
            )
        ]
    )
