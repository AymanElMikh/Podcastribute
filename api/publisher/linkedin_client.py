"""LinkedIn API client for direct post publishing via OAuth 2.0.

Users connect their LinkedIn account via OAuth in Settings.
Posts directly to the LinkedIn UGC Posts API without Buffer.
"""

import httpx
import structlog

log = structlog.get_logger(__name__)

LINKEDIN_API_BASE: str = "https://api.linkedin.com/v2"


class LinkedInClient:
    """Publishes posts directly to LinkedIn using the UGC Posts API.

    Requires a valid LinkedIn OAuth 2.0 access token with w_member_social scope.
    """

    def __init__(self, access_token: str, author_urn: str) -> None:
        """Initialize the LinkedIn client.

        Args:
            access_token: LinkedIn OAuth 2.0 access token.
            author_urn: LinkedIn member URN (urn:li:person:{id}).
        """
        self.access_token = access_token
        self.author_urn = author_urn

    async def publish_post(self, text: str) -> dict:
        """Publish a text post directly to LinkedIn.

        Args:
            text: Post content (LinkedIn supports up to 3000 chars).

        Returns:
            LinkedIn API response dict with post URN.

        Raises:
            httpx.HTTPStatusError: If LinkedIn returns a non-2xx response.
        """
        payload = {
            "author": self.author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": text,
                    },
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LINKEDIN_API_BASE}/ugcPosts",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0",
                },
            )
            response.raise_for_status()
            result = response.json()

        post_urn = result.get("id")
        log.info(
            "linkedin_post_published",
            author_urn=self.author_urn,
            post_urn=post_urn,
        )
        return result
