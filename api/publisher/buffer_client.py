"""Buffer API client for scheduling Twitter and LinkedIn posts.

Users connect their Buffer account via OAuth in Settings.
The encrypted access token is stored per user in the database.
"""

import httpx
import structlog

log = structlog.get_logger(__name__)

BUFFER_API_BASE: str = "https://api.bufferapp.com/1"


class BufferClient:
    """Schedules social media posts via the Buffer API.

    Supports Twitter and LinkedIn scheduling. Requires a valid
    Buffer OAuth access token for the user.
    """

    def __init__(self, access_token: str) -> None:
        """Initialize the Buffer client with a user's access token.

        Args:
            access_token: Buffer OAuth access token for the user.
        """
        self.access_token = access_token

    async def schedule_post(
        self,
        profile_id: str,
        text: str,
        scheduled_at: str | None = None,
    ) -> dict:
        """Schedule a post to a connected Buffer profile.

        Args:
            profile_id: Buffer social profile ID to post to.
            text: Post content text.
            scheduled_at: ISO 8601 timestamp for scheduled posting.
                          None queues the post at Buffer's optimal time.

        Returns:
            Buffer API response dict with post ID and status.

        Raises:
            httpx.HTTPStatusError: If Buffer returns a non-2xx response.
        """
        payload: dict = {
            "profile_ids[]": profile_id,
            "text": text,
            "access_token": self.access_token,
        }
        if scheduled_at is not None:
            payload["scheduled_at"] = scheduled_at

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BUFFER_API_BASE}/updates/create.json",
                data=payload,
            )
            response.raise_for_status()
            result = response.json()

        log.info(
            "buffer_post_scheduled",
            profile_id=profile_id,
            scheduled_at=scheduled_at,
            update_id=result.get("updates", [{}])[0].get("id"),
        )
        return result
