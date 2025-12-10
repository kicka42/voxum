"""Summary Agent."""

from dataclasses import dataclass
from pathlib import Path

import litellm

from voxum.agents.base import BaseAgent
from voxum.config import get_config


@dataclass
class SummaryInput:
    """Input for the summary agent."""

    transcript: str
    audio_path: Path


@dataclass
class SummaryOutput:
    """Output from the summary agent."""

    summary: str
    transcript: str
    audio_path: Path


class SummarizerAgent(BaseAgent[SummaryInput, SummaryOutput]):
    """Agent that summarizes meeting transcripts using LiteLLM.

    Takes a transcript and produces a structured summary with
    participants, key points, and action items.
    """

    def __init__(self):
        super().__init__("SummarizerAgent")
        self._prompt_template: str | None = None

    @property
    def prompt_template(self) -> str:
        """Get the summary prompt template, loading from file if needed."""
        if self._prompt_template is None:
            try:
                self._prompt_template = self.load_prompt("summarizer")
            except FileNotFoundError:
                self._prompt_template = """Analyze this meeting transcript and create a summary with:
- Participants
- Main discussion points
- Action items with owners
- Overall summary

Language: {language}"""
        return self._prompt_template

    def _build_prompt(self, transcript: str) -> str:
        """Build the full prompt with transcript and language."""
        config = get_config()
        prompt = self.prompt_template.format(language=config.summary_language)
        return f"{prompt}\n\n---\n\nTranscript:\n{transcript}"

    def _process(self, input_data: SummaryInput) -> SummaryOutput:
        """Summarize the transcript.

        Args:
            input_data: SummaryInput with transcript text

        Returns:
            SummaryOutput with structured summary
        """
        config = get_config()

        self.logger.info(f"Summarizing transcript ({len(input_data.transcript)} chars)")

        prompt = self._build_prompt(input_data.transcript)

        response = litellm.completion(
            model=config.summarization_model,
            messages=[{"role": "user", "content": prompt}],
        )

        summary = response.choices[0].message.content

        self.logger.info(f"Summary generated ({len(summary)} chars)")

        return SummaryOutput(
            summary=summary,
            transcript=input_data.transcript,
            audio_path=input_data.audio_path,
        )
