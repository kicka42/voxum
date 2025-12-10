"""Resend email."""

import logging
from dataclasses import dataclass

import resend

from voxum.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    """Email attachment."""

    filename: str
    content: str


def send_summary(
    subject: str,
    body: str,
    attachments: list[Attachment] | None = None,
    to: str | None = None,
    from_email: str | None = None,
) -> str:
    """Send an email via Resend.

    Args:
        subject: Email subject line
        body: Email body (plain text)
        attachments: Optional list of attachments
        to: Recipient email (defaults to config EMAIL_TO)
        from_email: Sender email (defaults to config EMAIL_FROM)

    Returns:
        Email ID from Resend
    """
    config = get_config()
    resend.api_key = config.resend_api_key

    to_addr = to or config.email_to
    from_addr = from_email or config.email_from

    params: dict = {
        "from": from_addr,
        "to": [to_addr],
        "subject": subject,
        "text": body,
    }

    if attachments:
        params["attachments"] = [
            {"filename": att.filename, "content": att.content}
            for att in attachments
        ]

    logger.info(f"Sending email to {to_addr}: {subject}")
    response = resend.Emails.send(params)

    email_id = response.get("id", "unknown")
    logger.info(f"Email sent: {email_id}")
    return email_id
