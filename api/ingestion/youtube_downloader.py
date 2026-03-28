"""YouTube audio downloader using yt-dlp.

Validates YouTube URLs before downloading and extracts the best-quality
audio track in MP3 format for transcription.
"""

import asyncio
import re
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

# Accepted YouTube URL patterns
_YOUTUBE_PATTERNS: list[re.Pattern] = [
    re.compile(r"^https?://(www\.)?youtube\.com/watch\?.*v=[\w-]+"),
    re.compile(r"^https?://youtu\.be/[\w-]+"),
    re.compile(r"^https?://(www\.)?youtube\.com/shorts/[\w-]+"),
    re.compile(r"^https?://(www\.)?youtube\.com/embed/[\w-]+"),
]


class DownloadError(Exception):
    """Raised when a YouTube audio download fails."""


class YouTubeDownloader:
    """Downloads audio from YouTube videos using yt-dlp.

    Always validates the URL format before attempting a download to prevent
    unnecessary network requests and provide clear error messages.
    """

    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """Return True if the URL matches a recognised YouTube URL format.

        Args:
            url: URL string to validate.

        Returns:
            True if the URL looks like a YouTube video URL.
        """
        return any(pattern.match(url) for pattern in _YOUTUBE_PATTERNS)

    async def download(self, url: str, output_dir: str) -> str:
        """Download the audio track from a YouTube video.

        Uses yt-dlp with --format bestaudio --extract-audio --audio-format mp3.
        Validates that the URL is a real YouTube URL before downloading.

        Output filename template: `%(id)s.%(ext)s` — the resulting MP3 is
        located by globbing the output directory after the download completes.

        Args:
            url: YouTube video URL to download audio from.
            output_dir: Directory path where the downloaded file will be saved.

        Returns:
            Absolute path to the downloaded MP3 file.

        Raises:
            DownloadError: If the URL is invalid or the download fails.
        """
        if not self.is_valid_youtube_url(url):
            raise DownloadError(
                f"Invalid YouTube URL: {url!r}. "
                "Expected a youtube.com/watch, youtu.be, or youtube.com/shorts URL."
            )

        output_template = str(Path(output_dir) / "%(id)s.%(ext)s")

        log.info("youtube_download_start", url=url, output_dir=output_dir)

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--format",
            "bestaudio",
            "--extract-audio",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "5",
            "--output",
            output_template,
            "--no-playlist",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace")
            log.error("youtube_download_failed", url=url, stderr=error_msg)
            raise DownloadError(
                f"yt-dlp exited with code {proc.returncode}: {error_msg}"
            )

        # Locate the downloaded MP3
        mp3_files = list(Path(output_dir).glob("*.mp3"))
        if not mp3_files:
            raise DownloadError(f"yt-dlp completed but no MP3 found in {output_dir}")

        result_path = str(mp3_files[0])
        log.info("youtube_download_done", url=url, path=result_path)
        return result_path
