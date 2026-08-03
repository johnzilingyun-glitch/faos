import asyncio
import logging
import datetime
from faos.core.events import EventBus, Event
from faos.core.runtime import SystemRuntime

logger = logging.getLogger("faos.cron")

class CronManager:
    """
    Background worker that runs scheduled tasks.
    In Phase 3, this is used for Daily Automatic Review (每日自动复盘) of positions.
    """
    def __init__(self, runtime: SystemRuntime, interval_seconds: int = 86400):
        self.runtime = runtime
        self.interval = interval_seconds
        self.running = False
        self.task = None

    def start(self):
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._loop())
            logger.info(f"CronManager started with interval {self.interval}s")

    def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()

    async def _loop(self):
        while self.running:
            try:
                # Simplification: Sleep for the interval. 
                # In production, this would use a real cron expression or check market close times.
                await asyncio.sleep(self.interval)
                
                logger.info("CronManager triggered scheduled run.")
                await self._run_daily_review()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in CronManager loop: {e}")
                await asyncio.sleep(60)
                
    async def _run_daily_review(self):
        """
        Retrieves current portfolio positions and triggers a deep analysis workflow for each.
        """
        if hasattr(self.runtime, 'portfolio_service'):
            summary = self.runtime.portfolio_service.get_account_summary()
            positions = summary.get("positions", [])
            for pos in positions:
                symbol = pos.get("symbol")
                if symbol:
                    logger.info(f"Cron: Triggering daily review for position: {symbol}")
                    # Dispatch to Planner by simulating a system message
                    event = Event(
                        type="TaskSubmitted",
                        source="CronManager",
                        payload={
                            "task_id": f"cron-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{symbol}",
                            "intent": f"全面分析和复盘 {symbol}",
                            "llm_config": {"model": "gemini-2.5-pro"}
                        }
                    )
                    await self.runtime.event_bus.publish(event)
                    # Don't flood the system, delay between tasks
                    await asyncio.sleep(10)
