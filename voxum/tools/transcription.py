"""Audio transcription using LiteLLM."""

import logging
import subprocess
import tempfile
from pathlib import Path

import litellm

from voxum.config import get_config

logger = logging.getLogger(__name__)


def _compress_audio(file_path: Path, bitrate: str) -> Path:
    """Compress audio to mp3 for smaller file size.

    Args:
        file_path: Path to the audio file
        bitrate: Audio bitrate (e.g., "40k")

    Returns path to compressed temp file.
    """
    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    temp_path = Path(temp_file.name)
    temp_file.close()

    logger.info(f"Compressing {file_path.name} to reduce file size...")

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(file_path),
            "-ac", "1",           # mono
            "-ar", "16000",       # 16kHz sample rate (sufficient for speech)
            "-b:a", bitrate,
            str(temp_path)
        ],
        check=True,
        capture_output=True,
    )

    original_size = file_path.stat().st_size / (1024 * 1024)
    compressed_size = temp_path.stat().st_size / (1024 * 1024)
    logger.info(f"Compressed: {original_size:.1f}MB → {compressed_size:.1f}MB")

    return temp_path


def transcribe_file(file_path: Path) -> str:
    """Transcribe an audio file using LiteLLM.

    Supports OpenAI Whisper and Groq models.
    Automatically compresses files larger than the configured max size.

    Args:
        file_path: Path to the audio file

    Returns:
        Transcript text
    """
    config = get_config()
    temp_path = None

    max_file_size = config.transcription_max_file_size_mb * 1024 * 1024
    file_size = file_path.stat().st_size
    if file_size > max_file_size:
        logger.warning(
            f"File size ({file_size / (1024*1024):.1f}MB) exceeds limit, compressing..."
        )
        temp_path = _compress_audio(file_path, config.transcription_audio_bitrate)
        file_path = temp_path

    try:
        logger.info(f"Transcribing: {file_path.name} using {config.transcription_model}")

        with open(file_path, "rb") as audio_file:
            response = litellm.transcription(
                model=config.transcription_model,
                file=audio_file,
            )
        transcript = response.text

        logger.info(f"Transcription complete ({len(transcript)} chars)")

        return transcript
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()
