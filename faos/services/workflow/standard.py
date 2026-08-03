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
            WorkflowNodeDef(id="node1", capability="cap.fetch_data"),
            WorkflowNodeDef(id="node2", capability="cap.fetch_news"),
            WorkflowNodeDef(
                id="node3", 
                capability="cap.analyze", 
                dependencies=["node1", "node2"]
            ),
            WorkflowNodeDef(
                id="node_discuss",
                capability="cap.discuss",
                dependencies=["node3"]
            ),
            WorkflowNodeDef(
                id="node_decision", 
                capability="cap.decision", 
                dependencies=["node_discuss"]
            ),
            WorkflowNodeDef(
                id="node_reflection",
                capability="cap.reflection",
                dependencies=["node_decision"]
            ),
            WorkflowNodeDef(
                id="node4", 
                capability="cap.report", 
                dependencies=["node_reflection"]
            )
        ]
    )

def get_news_summary_workflow() -> WorkflowDefinition:
    """
    Workflow for purely summarizing recent news without heavy financial analysis.
    """
    return WorkflowDefinition(
        id="NewsSummaryWorkflow",
        name="News Summary Workflow",
        description="Fetch news for a symbol and generate a summary report. Good for 'summarize news' queries.",
        nodes=[
            WorkflowNodeDef(id="node1", capability="cap.fetch_news"),
            WorkflowNodeDef(
                id="node2",
                capability="cap.report",
                dependencies=["node1"]
            )
        ]
    )

def get_sector_scan_workflow() -> WorkflowDefinition:
    """
    Workflow for sector scanning and finding undervalued stocks.
    """
    return WorkflowDefinition(
        id="SectorScanWorkflow",
        name="Sector Scanning Workflow",
        description="Scan sectors, identify potential stock candidates, and perform comparative analysis to recommend the best picks.",
        nodes=[
            WorkflowNodeDef(id="node_scan", capability="cap.sector_scan"),
            WorkflowNodeDef(id="node_batch_data", capability="cap.batch_fetch_data", dependencies=["node_scan"]),
            WorkflowNodeDef(id="node_compare", capability="cap.compare_stocks", dependencies=["node_batch_data"]),
            WorkflowNodeDef(id="node_report", capability="cap.report", dependencies=["node_compare"])
        ]
    )

def get_backtest_workflow() -> WorkflowDefinition:
    """
    Standard Workflow for running historical backtests on a financial asset.
    """
    return WorkflowDefinition(
        id="BacktestWorkflow",
        name="Backtest Workflow",
        description="Run historical backtests on a stock to evaluate trading performance. Good for 'backtest' queries.",
        nodes=[
            WorkflowNodeDef(id="init_backtest", capability="cap.init_backtest"),
            WorkflowNodeDef(
                id="run_backtest_loop",
                capability="cap.run_backtest_loop",
                dependencies=["init_backtest"]
            ),
            WorkflowNodeDef(
                id="generate_report",
                capability="cap.report",
                dependencies=["run_backtest_loop"]
            )
        ]
    )
