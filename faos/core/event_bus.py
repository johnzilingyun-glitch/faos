import asyncio
from typing import Callable, Dict, List, Awaitable
import logging
from faos.core.models import Event

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task = None

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    async def publish(self, event: Event):
        await self._queue.put(event)
        logger.debug(f"Published event {event.type} from {event.source}")

    async def _worker(self):
        while self._running:
            event = await self._queue.get()
            handlers = self._subscribers.get(event.type, [])
            wildcard_handlers = self._subscribers.get("*", [])
            all_handlers = handlers + wildcard_handlers
            
            for handler in all_handlers:
                try:
                    # Execute handlers concurrently
                    asyncio.create_task(handler(event))
                except Exception as e:
                    logger.error(f"Error executing handler for {event.type}: {e}")
            self._queue.task_done()

    def start(self):
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("EventBus started")

    async def stop(self):
        if self._running:
            self._running = False
            # Wait for queue to process remaining items
            await self._queue.join()
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("EventBus stopped")
