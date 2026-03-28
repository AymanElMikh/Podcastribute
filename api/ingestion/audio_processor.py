"""Audio processing utilities — WAV conversion and Whisper transcription.

All audio processing runs in Celery workers, never in FastAPI request handlers.
"""

import asyncio
import json
from pathlib import Path

import structlog

from api.config import settings
from api.models.episode import TranscriptResult

log = structlog.get_logger(__name__)


class TranscriptionError(Exception):
    """Raised when Whisper transcription fails."""


class AudioConversionError(Exception):
    """Raised when ffmpeg audio conversion fails."""


class AudioProcessor:
    """Handles WAV conversion and speech-to-text transcription via Whisper.

    Whisper is invoked as a subprocess to avoid blocking the async event loop.
    ffmpeg is used for pre-processing audio to the format Whisper expects.
    """

    async def transcribe(self, audio_path: str) -> TranscriptResult:
        """Transcribe an audio file using the configured Whisper model.

        Runs `whisper {path} --model {model} --output_format json` as a
        subprocess, parses the output JSON, and returns structured data.

        The Whisper CLI writes `{stem}.json` alongside the input file.

        Args:
            audio_path: Absolute path to the audio file to transcribe.

        Returns:
            TranscriptResult with text, word-level segments, duration, and language.

        Raises:
            TranscriptionError: If the Whisper subprocess exits with a non-zero code.
        """
        path = Path(audio_path)
        output_dir = str(path.parent)

        log.info("transcription_start", audio_path=audio_path, model=settings.WHISPER_MODEL)

        proc = await asyncio.create_subprocess_exec(
            "whisper",
            audio_path,
            "--model",
            settings.WHISPER_MODEL,
            "--output_format",
            "json",
            "--output_dir",
            output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace")
            log.error("transcription_failed", returncode=proc.returncode, stderr=error_msg)
            raise TranscriptionError(f"Whisper exited with code {proc.returncode}: {error_msg}")

        json_path = path.parent / (path.stem + ".json")
        if not json_path.exists():
            raise TranscriptionError(f"Whisper output not found at {json_path}")

        data = json.loads(json_path.read_text(encoding="utf-8"))
        segments: list[dict] = data.get("segments", [])
        duration = int(segments[-1]["end"]) if segments else 0

        log.info(
            "transcription_done",
            audio_path=audio_path,
            duration_seconds=duration,
            language=data.get("language", "unknown"),
        )

        return TranscriptResult(
            text=data.get("text", "").strip(),
            segments=segments,
            duration_seconds=duration,
            language=data.get("language", "en"),
        )

    async def convert_to_wav(self, input_path: str) -> str:
        """Convert an audio file to 16 kHz mono WAV format using ffmpeg.

        Required for optimal Whisper transcription accuracy. Overwrites any
        existing WAV file at the output path (-y flag).

        Args:
            input_path: Path to the source audio file.

        Returns:
            Path to the converted WAV file (same directory, `.wav` extension).

        Raises:
            AudioConversionError: If ffmpeg exits with a non-zero code.
        """
        output_path = str(Path(input_path).with_suffix(".wav"))

        log.info("audio_conversion_start", input=input_path, output=output_path)

        proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-i",
            input_path,
            "-ar",
            "16000",
            "-ac",
            "1",
            output_path,
            "-y",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode(errors="replace")
            log.error("audio_conversion_failed", returncode=proc.returncode, stderr=error_msg)
            raise AudioConversionError(
                f"ffmpeg exited with code {proc.returncode}: {error_msg}"
            )

        log.info("audio_conversion_done", output=output_path)
        return output_path
