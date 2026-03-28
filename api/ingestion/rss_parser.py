"""RSS feed parser for podcast episode ingestion.

Fetches and parses RSS/Atom feeds to extract episode metadata and audio URLs,
then downloads audio files for transcription.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import feedparser
import httpx
import structlog
from pydantic import BaseModel

log = structlog.get_logger(__name__)

# Audio MIME types accepted as podcast enclosures
_AUDIO_MIME_PREFIXES = ("audio/",)


def _is_audio_enclosure(enclosure: dict) -> bool:
    """Return True if the enclosure looks like an audio file."""
    mime = enclosure.get("type", "")
    return any(mime.startswith(prefix) for prefix in _AUDIO_MIME_PREFIXES)


def _parse_published(entry: dict) -> datetime | None:
    """Parse the published_parsed tuple from a feedparser entry."""
    import time

    tp = entry.get("published_parsed") or entry.get("updated_parsed")
    if tp is None:
        return None
    try:
        return datetime.fromtimestamp(time.mktime(tp))
    except (OverflowError, ValueError):
        return None


class RSSEpisode(BaseModel):
    """Metadata and local file path for a single RSS feed episode."""

    title: str
    audio_path: str
    published_at: datetime | None
    episode_url: str | None


class RSSParser:
    """Parses RSS podcast feeds and downloads episode audio files.

    Uses httpx for async HTTP requests and feedparser for feed parsing.
    feedparser itself is synchronous and is run in a thread executor to
    avoid blocking the event loop.
    """

    async def _fetch_feed(self, feed_url: str) -> feedparser.FeedParserDict:
        """Fetch and parse an RSS feed asynchronously.

        Args:
            feed_url: URL of the RSS feed.

        Returns:
            Parsed feedparser dictionary.

        Raises:
            ValueError: If the feed cannot be fetched or parsed.
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(feed_url)
            resp.raise_for_status()
            raw = resp.text

        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, raw)

        if feed.bozo and not feed.entries:
            raise ValueError(f"Failed to parse RSS feed: {feed_url}")

        return feed

    @staticmethod
    def _audio_url_from_entry(entry: dict) -> str | None:
        """Extract the first audio enclosure URL from a feed entry."""
        for enclosure in entry.get("enclosures", []):
            if _is_audio_enclosure(enclosure):
                return enclosure.get("href") or enclosure.get("url")
        # Fallback: some feeds use links
        for link in entry.get("links", []):
            if _is_audio_enclosure(link):
                return link.get("href")
        return None

    async def _download_audio(self, audio_url: str, dest_dir: str) -> str:
        """Stream an audio file from a URL to a local directory.

        Args:
            audio_url: Direct URL of the audio file.
            dest_dir: Directory to save the downloaded file.

        Returns:
            Local path to the downloaded file.

        Raises:
            httpx.HTTPError: On network or HTTP errors.
        """
        filename = Path(audio_url.split("?")[0]).name or "episode.mp3"
        dest_path = Path(dest_dir) / filename

        async with httpx.AsyncClient(timeout=300.0, follow_redirects=True) as client:
            async with client.stream("GET", audio_url) as resp:
                resp.raise_for_status()
                with open(dest_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=65536):
                        f.write(chunk)

        log.info("rss_audio_downloaded", url=audio_url, path=str(dest_path))
        return str(dest_path)

    async def get_latest_episode(self, feed_url: str) -> RSSEpisode:
        """Fetch and download the most recent episode from an RSS feed.

        Finds the most recent item with an audio enclosure, downloads the
        audio file to a temp directory, and returns episode metadata.

        Args:
            feed_url: URL of the podcast RSS feed.

        Returns:
            RSSEpisode with title, local audio_path, and metadata.

        Raises:
            ValueError: If the feed has no audio episodes.
        """
        feed = await self._fetch_feed(feed_url)
        audio_url: str | None = None
        title = "Untitled Episode"
        episode_url: str | None = None
        published_at: datetime | None = None

        for entry in feed.entries:
            candidate = self._audio_url_from_entry(entry)
            if candidate:
                audio_url = candidate
                title = entry.get("title", "Untitled Episode")
                episode_url = entry.get("link")
                published_at = _parse_published(entry)
                break

        if not audio_url:
            raise ValueError(f"No audio episodes found in feed: {feed_url}")

        tmp_dir = tempfile.mkdtemp(prefix="podcast_rss_")
        audio_path = await self._download_audio(audio_url, tmp_dir)

        return RSSEpisode(
            title=title,
            audio_path=audio_path,
            published_at=published_at,
            episode_url=episode_url,
        )

    async def list_episodes(self, feed_url: str, limit: int = 10) -> list[RSSEpisode]:
        """Fetch metadata for the N most recent episodes from an RSS feed.

        Does NOT download audio files — only returns metadata so the user
        can choose which episode to process.

        Args:
            feed_url: URL of the podcast RSS feed.
            limit: Maximum number of episodes to return.

        Returns:
            List of RSSEpisode objects (audio_path is empty string — not downloaded).
        """
        feed = await self._fetch_feed(feed_url)
        results: list[RSSEpisode] = []

        for entry in feed.entries[:limit]:
            audio_url = self._audio_url_from_entry(entry)
            if audio_url is None:
                continue

            results.append(
                RSSEpisode(
                    title=entry.get("title", "Untitled Episode"),
                    audio_path="",  # not downloaded at listing stage
                    published_at=_parse_published(entry),
                    episode_url=entry.get("link"),
                )
            )

        return results
