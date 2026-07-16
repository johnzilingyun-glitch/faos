import logging
from typing import Dict, Any

from faos.services.report.models import ReportRequest, ReportResponse
from faos.services.report.builder import ReportBuilder
from faos.services.report.renderers import MarkdownRenderer, JsonRenderer

logger = logging.getLogger(__name__)

class ReportService:
    """
    Report Service is responsible for final output generation.
    It takes context data, builds a Report object, and renders it to the requested format.
    """
    def __init__(self):
        self.builder = ReportBuilder()
        
        # Initialize renderers
        self.renderers = {
            "markdown": MarkdownRenderer(),
            "json": JsonRenderer()
        }
        logger.info("ReportService initialized")

    async def generate(self, request: ReportRequest) -> ReportResponse:
        logger.info(f"ReportService generating report for task {request.task_id} in {request.format} format")
        
        try:
            # 1. Build standardized Report object
            report_obj = self.builder.build(request.task_id, request.context_data)
            
            # 2. Find correct Renderer
            fmt = request.format.lower()
            renderer = self.renderers.get(fmt)
            
            if not renderer:
                error_msg = f"Unsupported report format: {request.format}"
                logger.error(error_msg)
                return ReportResponse(format=request.format, content="", status="failed", error=error_msg)
                
            # 3. Render
            content = renderer.render(report_obj)
            return ReportResponse(format=fmt, content=content)
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return ReportResponse(format=request.format, content="", status="failed", error=str(e))

