import json
import asyncio
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, List, Set, Optional

class EventService:
    """Pub/sub event broker providing Server-Sent Events (SSE) for live task evaluations."""

    def __init__(self, max_history: int = 200):
        self._subscribers: Set[asyncio.Queue] = set()
        self._history: List[Dict[str, Any]] = []
        self._max_history = max_history

    def publish(
        self,
        event_type: str,
        data: Dict[str, Any],
        task_id: Optional[str] = None,
    ):
        """Broadcast an event to all connected SSE clients and record in history."""
        payload = {
            "event": event_type,
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        # Store in rolling buffer
        self._history.append(payload)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # Broadcast to all active queues
        raw_sse = f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
        dead_subscribers = set()

        for queue in self._subscribers:
            try:
                queue.put_nowait(raw_sse)
            except asyncio.QueueFull:
                dead_subscribers.add(queue)

        for dead in dead_subscribers:
            self._subscribers.discard(dead)

    async def subscribe(self) -> AsyncGenerator[str, None]:
        """Subscribe to live SSE events stream."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(queue)

        try:
            # Yield initial connection confirmation
            init_payload = {
                "event": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {"message": "Connected to TRIPWIRE live event stream"},
            }
            yield f"event: connected\ndata: {json.dumps(init_payload)}\n\n"

            while True:
                msg = await queue.get()
                yield msg
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            self._subscribers.discard(queue)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return snapshot of most recent event payloads."""
        return self._history[-limit:]

event_service = EventService()

