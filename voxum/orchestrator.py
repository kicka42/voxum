"""Coordinates the agent pipeline."""

import logging
from dataclasses import dataclass
from pathlib import Path

from voxum.agents.transcriber import TranscriberAgent, TranscriptionInput
from voxum.agents.summarizer import SummarizerAgent, SummaryInput
from voxum.agents.delivery import DeliveryAgent, DeliveryInput, DeliveryOutput

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result from processing a file through the pipeline."""

    success: bool
    error: str | None = None
    delivery_output: DeliveryOutput | None = None


class Orchestrator:
    """Coordinates the agent pipeline for processing audio files.

    Pipeline: Transcriber → Summarizer → Delivery
    """

    def __init__(self):
        self.transcriber = TranscriberAgent()
        self.summarizer = SummarizerAgent()
        self.delivery = DeliveryAgent()

    def process_file(
        self,
        file_path: Path,
        original_filename: str | None = None,
        drive_file_id: str | None = None,
    ) -> ProcessingResult:
        """Process an audio file through the full pipeline.

        Args:
            file_path: Path to the audio file (local or downloaded)
            original_filename: Original filename (for naming outputs)
            drive_file_id: Google Drive file ID (if from Drive)

        Returns:
            ProcessingResult with success status and outputs
        """
        if original_filename is None:
            original_filename = file_path.name

        logger.info(f"Starting pipeline for: {original_filename}")

        # Stage 1: Transcription
        logger.info("Stage 1: Transcription")
        transcription_result = self.transcriber.process(
            TranscriptionInput(audio_path=file_path)
        )

        if not transcription_result.success:
            logger.error(f"Transcription failed: {transcription_result.error}")
            return ProcessingResult(
                success=False,
                error=f"Transcription failed: {transcription_result.error}",
            )

        transcript = transcription_result.output.transcript
        logger.info(f"Transcription complete: {len(transcript)} chars")

        # Stage 2: Summarization
        logger.info("Stage 2: Summarization")
        summary_result = self.summarizer.process(
            SummaryInput(transcript=transcript, audio_path=file_path)
        )

        if not summary_result.success:
            logger.error(f"Summarization failed: {summary_result.error}")
            return ProcessingResult(
                success=False,
                error=f"Summarization failed: {summary_result.error}",
            )

        summary = summary_result.output.summary
        logger.info(f"Summary complete: {len(summary)} chars")

        # Stage 3: Delivery
        logger.info("Stage 3: Delivery")
        delivery_result = self.delivery.process(
            DeliveryInput(
                summary=summary,
                transcript=transcript,
                audio_path=file_path,
                original_filename=original_filename,
                drive_file_id=drive_file_id,
            )
        )

        if not delivery_result.success:
            logger.error(f"Delivery failed: {delivery_result.error}")
            return ProcessingResult(
                success=False,
                error=f"Delivery failed: {delivery_result.error}",
            )

        logger.info(f"Pipeline complete for: {original_filename}")
        return ProcessingResult(
            success=True,
            delivery_output=delivery_result.output,
        )
