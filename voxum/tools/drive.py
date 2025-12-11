"""Google Drive API operations."""

import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from voxum.config import get_config

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_token_file() -> Path:
    """Get path to token file from config."""
    return get_config().voxum_state_dir / "token.json"


def _get_processed_file() -> Path:
    """Get path to processed file from config."""
    return get_config().voxum_state_dir / "processed.json"

AUDIO_MIME_TYPES = [
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/flac",
    "audio/mp4",
    "audio/x-m4a",
    "audio/webm",
]


def _ensure_voxum_dir() -> None:
    """Ensure voxum state directory exists."""
    get_config().voxum_state_dir.mkdir(parents=True, exist_ok=True)


def authenticate() -> Credentials:
    """Run OAuth flow and return credentials.

    Opens browser for user to authenticate with Google.
    Stores refresh token for future use.

    Returns:
        Credentials: Google OAuth credentials
    """
    _ensure_voxum_dir()
    config = get_config()
    creds = None
    token_file = _get_token_file()

    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("Starting OAuth flow - browser will open")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.google_client_secrets_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        token_file.write_text(creds.to_json())
        logger.info(f"Credentials saved to {token_file}")

    return creds


def get_drive_service():
    """Get authenticated Google Drive service."""
    creds = authenticate()
    return build("drive", "v3", credentials=creds)


def list_new_files(folder_id: str, since_timestamp: datetime | None = None) -> list[dict]:
    """List audio files in a Drive folder.

    Args:
        folder_id: Google Drive folder ID
        since_timestamp: Only return files modified after this time

    Returns:
        List of file metadata dicts with id, name, mimeType, modifiedTime
    """
    service = get_drive_service()

    mime_query = " or ".join(f"mimeType='{mt}'" for mt in AUDIO_MIME_TYPES)
    query = f"'{folder_id}' in parents and ({mime_query}) and trashed=false"

    if since_timestamp:
        timestamp_str = since_timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        query += f" and modifiedTime > '{timestamp_str}'"

    results = (
        service.files()
        .list(
            q=query,
            fields="files(id, name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc",
        )
        .execute()
    )

    files = results.get("files", [])
    logger.info(f"Found {len(files)} audio files in folder")
    return files


def download_file(file_id: str, filename: str | None = None) -> Path:
    """Download a file from Google Drive to a temp location.

    Args:
        file_id: Google Drive file ID
        filename: Optional filename to use (for extension detection)

    Returns:
        Path to downloaded file in temp directory
    """
    service = get_drive_service()

    if filename is None:
        file_meta = service.files().get(fileId=file_id, fields="name").execute()
        filename = file_meta["name"]

    suffix = Path(filename).suffix or ".mp3"
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = Path(temp_file.name)

    request = service.files().get_media(fileId=file_id)

    with open(temp_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download {int(status.progress() * 100)}%")

    logger.info(f"Downloaded {filename} to {temp_path}")
    return temp_path


def upload_file(folder_id: str, filename: str, content: str) -> str:
    """Upload a text file to Google Drive.

    Args:
        folder_id: Google Drive folder ID
        filename: Name for the uploaded file
        content: Text content to upload

    Returns:
        File ID of uploaded file
    """
    service = get_drive_service()

    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write(content)
        temp_path = Path(f.name)

    file_metadata = {"name": filename, "parents": [folder_id]}

    media = MediaFileUpload(str(temp_path), mimetype="text/plain")

    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    temp_path.unlink()

    file_id = file.get("id")
    logger.info(f"Uploaded {filename} with ID {file_id}")
    return file_id


def get_processed_files() -> set[str]:
    """Get set of already processed file IDs.

    Returns:
        Set of file IDs that have been processed
    """
    _ensure_voxum_dir()
    processed_file = _get_processed_file()

    if not processed_file.exists():
        return set()

    data = json.loads(processed_file.read_text())
    return set(data.get("processed", []))


def mark_processed(file_id: str) -> None:
    """Mark a file as processed.

    Args:
        file_id: Google Drive file ID to mark as processed
    """
    _ensure_voxum_dir()
    processed = get_processed_files()
    processed.add(file_id)

    processed_file = _get_processed_file()
    processed_file.write_text(json.dumps({"processed": list(processed)}))
    logger.debug(f"Marked {file_id} as processed")


def is_processed(file_id: str) -> bool:
    """Check if a file has been processed.

    Args:
        file_id: Google Drive file ID

    Returns:
        True if file has been processed
    """
    return file_id in get_processed_files()
