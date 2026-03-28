"""Audio processing utilities — WAV conversion and Whisper transcription.

All audio processing runs in Celery workers, never in FastAPI request handlers.
"""

import asyncio
from pathlib import Path

import structlog

from api.config import settings
from api.models.episode import TranscriptResult

log = structlog.get_logger(__name__)

WHISPER_MODEL_DIR = "/tmp/whisper_models"


class TranscriptionError(Exception):
    """Raised when Whisper transcription fails."""


class AudioConversionError(Exception):
    """Raised when ffmpeg audio conversion fails."""


def _load_whisper_model():
    """Load the faster-whisper model (CPU, int8 quantization).

    Called once per worker process. Returns a WhisperModel instance
    ready for transcription.
    """
    from faster_whisper import WhisperModel

    return WhisperModel(
        settings.WHISPER_MODEL,
        device="cpu",
        compute_type="int8",
        download_root=WHISPER_MODEL_DIR,
    )


# Module-level cache — loaded on first transcription call within a worker process
_whisper_model = None


class AudioProcessor:
    """Handles WAV conversion and speech-to-text transcription via faster-whisper.

    faster-whisper uses CTranslate2 under the hood for 4x faster inference
    than openai-whisper on the same CPU, with int8 quantization.
    """

    def _get_model(self):
        """Return the cached WhisperModel, loading it on first call."""
        global _whisper_model
        if _whisper_model is None:
            log.info("whisper_model_loading", model=settings.WHISPER_MODEL)
            _whisper_model = _load_whisper_model()
            log.info("whisper_model_ready", model=settings.WHISPER_MODEL)
        return _whisper_model

    async def transcribe(self, audio_path: str) -> TranscriptResult:
        """Transcribe an audio file using faster-whisper.

        Runs the transcription in a thread pool executor to avoid blocking
        the async event loop during CPU-bound inference.

        Args:
            audio_path: Absolute path to the audio file to transcribe.

        Returns:
            TranscriptResult with text, word-level segments, duration, and language.

        Raises:
            TranscriptionError: If transcription fails.
        """
        log.info("transcription_start", audio_path=audio_path, model=settings.WHISPER_MODEL)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, self._run_transcription, audio_path)
        except Exception as exc:
            log.error("transcription_failed", audio_path=audio_path, error=str(exc))
            raise TranscriptionError(f"Transcription failed: {exc}") from exc

        log.info(
            "transcription_done",
            audio_path=audio_path,
            duration_seconds=result.duration_seconds,
            language=result.language,
        )
        return result

    def _run_transcription(self, audio_path: str) -> TranscriptResult:
        """Run faster-whisper inference synchronously (called in executor).

        Args:
            audio_path: Path to the audio file.

        Returns:
            TranscriptResult with text, segments, duration, and language.
        """
        model = self._get_model()
        segments_iter, info = model.transcribe(audio_path, beam_size=5)

        segments = []
        full_text_parts = []
        for seg in segments_iter:
            segments.append(
                {
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                }
            )
            full_text_parts.append(seg.text)

        full_text = " ".join(full_text_parts).strip()
        duration = int(info.duration) if info.duration else (
            int(segments[-1]["end"]) if segments else 0
        )

        return TranscriptResult(
            text=full_text,
            segments=segments,
            duration_seconds=duration,
            language=info.language,
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
