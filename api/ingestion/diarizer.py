"""Speaker diarization — identifies and separates different speakers in audio.

Assigns speaker labels to transcript segments to enable per-speaker
voice analysis and content attribution.
"""

import structlog

log = structlog.get_logger(__name__)


class Diarizer:
    """Performs speaker diarization on audio to separate speaker segments.

    Produces labelled segments that can be cross-referenced with the
    Whisper transcript to build per-speaker content.
    """

    async def diarize(self, audio_path: str) -> list[dict]:
        """Identify distinct speakers in an audio file and segment the timeline.

        Args:
            audio_path: Absolute path to the audio file.

        Returns:
            List of dicts: [{speaker, start, end}] with speaker labels
            (SPEAKER_00, SPEAKER_01, etc.) and timestamps in seconds.
        """
        raise NotImplementedError("Implemented in Phase 3")
