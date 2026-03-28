"""SSE (Server-Sent Events) streaming utilities for real-time progress updates.

Publishes events to Redis pub/sub channels and provides an async generator
for streaming those events to frontend EventSource connections.
"""

import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone

import structlog

log = structlog.get_logger(__name__)

CHANNEL_PREFIX: str = "podcast:"
EVENT_TTL: int = 7200  # 2 hours in seconds

EVENT_TYPES: dict[str, str] = {
    "upload_received": "Episode received, preparing...",
    "transcription_start": "Transcribing audio...",
    "transcription_done": "Transcription complete ({duration})",
    "moments_detected": "Found {count} great moments",
    "generating_content": "Generating {formats} content formats...",
    "content_ready": "All content ready for review!",
    "error": "Processing failed: {message}",
}

TERMINAL_EVENTS: frozenset[str] = frozenset({"content_ready", "error"})


async def emit_event(
    redis: object,
    session_id: str,
    event_type: str,
    data: dict | None = None,
) -> None:
    """Publish a typed SSE event to the session's Redis pub/sub channel.

    A no-op when redis is None (e.g. during testing or when SSE is not
    yet wired), so callers never need to guard against an unavailable client.

    Args:
        redis: Async Redis client instance, or None to skip publishing.
        session_id: Unique session identifier for the processing job.
        event_type: One of the keys defined in EVENT_TYPES.
        data: Optional additional payload to include in the event.
    """
    if redis is None:
        log.debug("emit_event_skipped_no_redis", session_id=session_id, event_type=event_type)
        return

    event = {
        "type": event_type,
        "data": data or {},
        "label": EVENT_TYPES.get(event_type, event_type),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    channel = f"{CHANNEL_PREFIX}{session_id}"
    await redis.publish(channel, json.dumps(event))
    log.debug("event_emitted", session_id=session_id, event_type=event_type, channel=channel)


async def event_stream(
    redis: object, session_id: str
) -> AsyncIterator[str]:
    """Subscribe to a session channel and yield SSE-formatted event strings.

    Terminates automatically when a terminal event (content_ready or error)
    is received. Always unsubscribes and closes the pubsub on exit.

    Args:
        redis: Async Redis client instance.
        session_id: Session identifier whose channel to subscribe to.

    Yields:
        SSE-formatted strings: "data: {json}\\n\\n"
    """
    channel = f"{CHANNEL_PREFIX}{session_id}"
    pubsub = redis.pubsub()
    await pubsub.subscribe(channel)
    log.info("sse_subscribed", session_id=session_id, channel=channel)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            raw: str | bytes = message["data"]
            data = raw.decode() if isinstance(raw, bytes) else raw
            yield f"data: {data}\n\n"

            try:
                event = json.loads(data)
                if event.get("type") in TERMINAL_EVENTS:
                    log.info(
                        "sse_stream_ended",
                        session_id=session_id,
                        terminal_event=event["type"],
                    )
                    break
            except json.JSONDecodeError:
                log.warning("sse_invalid_json", session_id=session_id, raw=data[:200])
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.aclose()
        log.info("sse_unsubscribed", session_id=session_id, channel=channel)
