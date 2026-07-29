import asyncio
from typing import Callable, Dict, List, Awaitable, Set
import logging
from faos.core.models import Event

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task = None
        # Track in-flight handler tasks so exceptions are never lost and
        # stop() can drain them gracefully.
        self._handler_tasks: Set[asyncio.Task] = set()

    def subscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Awaitable[None]]):
        """Remove a previously registered handler (no-op if absent)."""
        handlers = self._subscribers.get(event_type)
        if handlers and handler in handlers:
            handlers.remove(handler)
            logger.debug(f"Unsubscribed handler from {event_type}")

    async def publish(self, event: Event):
        await self._queue.put(event)
        logger.debug(f"Published event {event.type} from {event.source}")

    async def _run_handler(self, handler: Callable[[Event], Awaitable[None]], event: Event):
        """Execute one handler, capturing exceptions so they never die silently."""
        try:
            await handler(event)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Error executing handler for {event.type}: {e}", exc_info=True)

    async def _worker(self):
        while self._running:
            event = await self._queue.get()
            handlers = self._subscribers.get(event.type, [])
            wildcard_handlers = self._subscribers.get("*", [])
            all_handlers = handlers + wildcard_handlers

            for handler in all_handlers:
                # Execute handlers concurrently, but keep a strong reference
                # so tasks are not garbage-collected mid-flight.
                task = asyncio.create_task(self._run_handler(handler, event))
                self._handler_tasks.add(task)
                task.add_done_callback(self._handler_tasks.discard)
            self._queue.task_done()

    def start(self):
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker())
            logger.info("EventBus started")

    async def stop(self):
        if self._running:
            self._running = False
            # Wait for queued events to be dispatched
            await self._queue.join()
            # Drain in-flight handler tasks (bounded wait, then cancel)
            if self._handler_tasks:
                done, pending = await asyncio.wait(self._handler_tasks, timeout=5.0)
                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("EventBus stopped")
