"""Beehiiv API client for creating newsletter post drafts.

Users connect their Beehiiv publication via API key in Settings.
"""

import httpx
import structlog

log = structlog.get_logger(__name__)

BEEHIIV_API_BASE: str = "https://api.beehiiv.com/v2"


class BeehiivClient:
    """Creates newsletter post drafts via the Beehiiv API.

    Requires the user's Beehiiv API key and publication ID.
    """

    def __init__(self, api_key: str, publication_id: str) -> None:
        """Initialize the Beehiiv client.

        Args:
            api_key: Beehiiv API key for the user's account.
            publication_id: Target Beehiiv publication ID.
        """
        self.api_key = api_key
        self.publication_id = publication_id

    async def create_draft(
        self,
        subject: str,
        body_html: str,
        preview_text: str | None = None,
    ) -> dict:
        """Create a newsletter post draft in Beehiiv.

        Args:
            subject: Email subject line.
            body_html: HTML-formatted email body content.
            preview_text: Email preview text shown in inbox.

        Returns:
            Beehiiv API response dict with post ID and status.

        Raises:
            httpx.HTTPStatusError: If Beehiiv returns a non-2xx response.
        """
        payload: dict = {
            "subject": subject,
            "body": body_html,
            "status": "draft",
        }
        if preview_text:
            payload["preview_text"] = preview_text

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BEEHIIV_API_BASE}/publications/{self.publication_id}/posts",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            result = response.json()

        post_id = result.get("data", {}).get("id")
        log.info(
            "beehiiv_draft_created",
            publication_id=self.publication_id,
            post_id=post_id,
            subject=subject,
        )
        return result
