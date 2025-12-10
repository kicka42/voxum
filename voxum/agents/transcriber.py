"""Transcription Agent."""

from dataclasses import dataclass
from pathlib import Path

from voxum.agents.base import BaseAgent
from voxum.tools import transcription


@dataclass
class TranscriptionInput:
    """Input for the transcription agent."""

    audio_path: Path


@dataclass
class TranscriptionOutput:
    """Output from the transcription agent."""

    transcript: str
    audio_path: Path


class TranscriberAgent(BaseAgent[TranscriptionInput, TranscriptionOutput]):
    """Agent that transcribes audio files using OpenAI Whisper via LiteLLM.

    Takes an audio file path and returns a transcript.
    """

    def __init__(self):
        super().__init__("TranscriberAgent")

    def _process(self, input_data: TranscriptionInput) -> TranscriptionOutput:
        """Transcribe the audio file.

        Args:
            input_data: TranscriptionInput with audio file path

        Returns:
            TranscriptionOutput with transcript text
        """
        self.logger.info(f"Transcribing: {input_data.audio_path.name}")

        transcript = transcription.transcribe_file(input_data.audio_path)

        return TranscriptionOutput(
            transcript=transcript,
            audio_path=input_data.audio_path,
        )
