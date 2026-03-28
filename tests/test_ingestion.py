"""Tests for the ingestion pipeline — audio processor, YouTube downloader, and upload API."""

import json
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.db.models import User
from api.dependencies import get_current_user
from api.ingestion.audio_processor import AudioConversionError, AudioProcessor, TranscriptionError
from api.ingestion.youtube_downloader import DownloadError, YouTubeDownloader
from api.main import app
from api.v1.auth import _hash_password


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_user() -> User:
    """A minimal User instance with a pre-set UUID for dependency overrides.

    The UUID must be set explicitly because SQLAlchemy's column default only
    fires at INSERT time; objects created outside a session have id=None.
    """
    return User(
        id=uuid.uuid4(),
        email="tester@example.com",
        hashed_password=_hash_password("pw"),
        plan="creator",
        episodes_this_month=0,
    )


@pytest.fixture
def authed_client(client: AsyncClient, fake_user: User):
    """AsyncClient with get_current_user overridden to return fake_user."""
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# AudioProcessor.transcribe()
# ---------------------------------------------------------------------------


async def test_transcribe_returns_transcript_result(tmp_path: Path) -> None:
    """transcribe() returns a TranscriptResult with text, segments, and language."""
    audio_file = tmp_path / "episode.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Whisper writes a .json file alongside the input
    whisper_output = tmp_path / "episode.json"
    whisper_output.write_text(
        json.dumps(
            {
                "text": " Hello world this is a test.",
                "segments": [
                    {"id": 0, "start": 0.0, "end": 3.5, "text": " Hello world"},
                    {"id": 1, "start": 3.5, "end": 7.0, "text": " this is a test."},
                ],
                "language": "en",
            }
        )
    )

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await AudioProcessor().transcribe(str(audio_file))

    assert result.text == "Hello world this is a test."
    assert len(result.segments) == 2
    assert result.language == "en"
    assert result.duration_seconds == 7


async def test_transcribe_raises_on_nonzero_exit(tmp_path: Path) -> None:
    """transcribe() raises TranscriptionError when Whisper exits non-zero."""
    audio_file = tmp_path / "bad.mp3"
    audio_file.write_bytes(b"not audio")

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"error: no model found"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(TranscriptionError):
            await AudioProcessor().transcribe(str(audio_file))


# ---------------------------------------------------------------------------
# AudioProcessor.convert_to_wav()
# ---------------------------------------------------------------------------


async def test_convert_to_wav_returns_wav_path(tmp_path: Path) -> None:
    """convert_to_wav() returns the path with .wav extension."""
    input_file = tmp_path / "audio.mp3"
    input_file.write_bytes(b"fake mp3")

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        result = await AudioProcessor().convert_to_wav(str(input_file))

    assert result == str(tmp_path / "audio.wav")


async def test_convert_to_wav_raises_on_failure(tmp_path: Path) -> None:
    """convert_to_wav() raises AudioConversionError on ffmpeg failure."""
    input_file = tmp_path / "audio.mp3"
    input_file.write_bytes(b"fake")

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"Invalid data found"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(AudioConversionError):
            await AudioProcessor().convert_to_wav(str(input_file))


# ---------------------------------------------------------------------------
# YouTubeDownloader — URL validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abc123",
        "https://youtube.com/watch?v=test&list=PLxxx",
    ],
)
def test_youtube_valid_urls(url: str) -> None:
    """is_valid_youtube_url() accepts legitimate YouTube URLs."""
    assert YouTubeDownloader.is_valid_youtube_url(url) is True


@pytest.mark.parametrize(
    "url",
    [
        "https://vimeo.com/123456",
        "https://not-youtube.com/watch?v=abc",
        "http://evil.com/youtu.be/abc",
        "ftp://youtube.com/watch?v=abc",
        "",
        "just some text",
    ],
)
def test_youtube_invalid_urls(url: str) -> None:
    """is_valid_youtube_url() rejects non-YouTube URLs."""
    assert YouTubeDownloader.is_valid_youtube_url(url) is False


async def test_youtube_download_raises_for_invalid_url() -> None:
    """download() raises DownloadError immediately for non-YouTube URLs."""
    with pytest.raises(DownloadError, match="Invalid YouTube URL"):
        await YouTubeDownloader().download("https://vimeo.com/123", "/tmp")


async def test_youtube_download_calls_yt_dlp(tmp_path: Path) -> None:
    """download() invokes yt-dlp and returns the path to the MP3."""
    # Create a fake mp3 so the glob finds it after the mocked yt-dlp "runs"
    (tmp_path / "dQw4w9WgXcQ.mp3").write_bytes(b"fake")

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc) as mock_exec:
        result = await YouTubeDownloader().download(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            str(tmp_path),
        )

    assert result.endswith(".mp3")
    mock_exec.assert_called_once()
    # yt-dlp was the first argument
    call_args = mock_exec.call_args[0]
    assert call_args[0] == "yt-dlp"


# ---------------------------------------------------------------------------
# Upload endpoint — MIME and size validation
# ---------------------------------------------------------------------------


async def test_upload_rejects_non_audio_mime(authed_client: AsyncClient) -> None:
    """POST /v1/episodes/upload returns 415 for non-audio MIME types."""
    with patch("worker.tasks.process_episode.delay"):
        resp = await authed_client.post(
            "/v1/episodes/upload",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )
    assert resp.status_code == 415


async def test_upload_rejects_oversized_file(
    authed_client: AsyncClient, tmp_path: Path
) -> None:
    """POST /v1/episodes/upload returns 413 when file exceeds MAX_UPLOAD_MB."""
    from api.config import settings

    # Temporarily lower the limit so we don't need a real huge file
    original = settings.MAX_UPLOAD_MB
    settings.MAX_UPLOAD_MB = 0  # 0 MB → any file is too large
    try:
        with patch("worker.tasks.process_episode.delay"):
            resp = await authed_client.post(
                "/v1/episodes/upload",
                files={"file": ("ep.mp3", b"audio bytes", "audio/mpeg")},
            )
        assert resp.status_code == 413
    finally:
        settings.MAX_UPLOAD_MB = original


async def test_upload_accepted_audio_file(
    authed_client: AsyncClient, tmp_path: Path
) -> None:
    """POST /v1/episodes/upload returns 202 and queues for valid audio."""
    from api.config import settings

    original_dir = settings.UPLOADS_DIR
    settings.UPLOADS_DIR = str(tmp_path)

    try:
        with patch("worker.tasks.process_episode.delay") as mock_delay:
            resp = await authed_client.post(
                "/v1/episodes/upload",
                files={"file": ("episode.mp3", b"fake audio", "audio/mpeg")},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "queued"
        assert data["source_type"] == "upload"
        mock_delay.assert_called_once()
    finally:
        settings.UPLOADS_DIR = original_dir


# ---------------------------------------------------------------------------
# YouTube ingest endpoint
# ---------------------------------------------------------------------------


async def test_youtube_ingest_rejects_invalid_url(authed_client: AsyncClient) -> None:
    """POST /v1/episodes/youtube returns 422 for non-YouTube URLs."""
    resp = await authed_client.post(
        "/v1/episodes/youtube",
        json={"url": "https://vimeo.com/123"},
    )
    assert resp.status_code == 422


async def test_youtube_ingest_accepted(authed_client: AsyncClient) -> None:
    """POST /v1/episodes/youtube returns 202 for a valid YouTube URL."""
    with patch("worker.tasks.process_episode.delay"):
        resp = await authed_client.post(
            "/v1/episodes/youtube",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    assert resp.status_code == 202
    assert resp.json()["source_type"] == "youtube"


# ---------------------------------------------------------------------------
# Episode list / detail
# ---------------------------------------------------------------------------


async def test_list_episodes_returns_empty(authed_client: AsyncClient) -> None:
    """GET /v1/episodes returns an empty list when user has no episodes."""
    resp = await authed_client.get("/v1/episodes")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_episode_not_found(authed_client: AsyncClient) -> None:
    """GET /v1/episodes/{id} returns 404 for unknown episode IDs."""
    import uuid

    resp = await authed_client.get(f"/v1/episodes/{uuid.uuid4()}")
    assert resp.status_code == 404
