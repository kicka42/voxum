"""Delivery Agent (Drive + Email)."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from voxum.agents.base import BaseAgent
from voxum.config import get_config
from voxum.tools import drive, email
from voxum.tools.email import Attachment


@dataclass
class DeliveryInput:
    """Input for the delivery agent."""

    summary: str
    transcript: str
    audio_path: Path
    original_filename: str
    drive_file_id: str | None = None


@dataclass
class DeliveryOutput:
    """Output from the delivery agent."""

    drive_file_id: str | None
    email_id: str | None
    summary_filename: str


class DeliveryAgent(BaseAgent[DeliveryInput, DeliveryOutput]):
    """Agent that delivers summaries via Google Drive and email.

    Uploads the summary to Google Drive and sends an email notification
    with the summary and transcript attached.
    """

    def __init__(self):
        super().__init__("DeliveryAgent")

    def _generate_summary_filename(self, original_filename: str) -> str:
        """Generate a filename for the summary file.

        Format: original_YYYY-MM-DD_summary.txt
        """
        stem = Path(original_filename).stem
        date_str = datetime.now().strftime("%Y-%m-%d")
        return f"{stem}_{date_str}_summary.txt"

    def _process(self, input_data: DeliveryInput) -> DeliveryOutput:
        """Deliver the summary via Drive and email.

        Args:
            input_data: DeliveryInput with summary, transcript, and metadata

        Returns:
            DeliveryOutput with file and email IDs
        """
        config = get_config()

        summary_filename = self._generate_summary_filename(input_data.original_filename)
        drive_file_id = None
        email_id = None

        # Upload to Google Drive
        if config.google_drive_folder_id:
            self.logger.info(f"Uploading summary to Drive: {summary_filename}")
            drive_file_id = drive.upload_file(
                folder_id=config.google_drive_folder_id,
                filename=summary_filename,
                content=input_data.summary,
            )

        # Send email notification
        subject = f"Meeting Summary: {input_data.original_filename}"

        attachments = [
            Attachment(filename=summary_filename, content=input_data.summary),
            Attachment(
                filename=f"{Path(input_data.original_filename).stem}_transcript.txt",
                content=input_data.transcript,
            ),
        ]

        self.logger.info(f"Sending email: {subject}")
        email_id = email.send_summary(
            subject=subject,
            body=input_data.summary,
            attachments=attachments,
        )

        # Mark original file as processed if it came from Drive
        if input_data.drive_file_id:
            drive.mark_processed(input_data.drive_file_id)

        return DeliveryOutput(
            drive_file_id=drive_file_id,
            email_id=email_id,
            summary_filename=summary_filename,
        )
