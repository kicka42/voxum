"""APScheduler background polling for Google Drive."""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from voxum.config import get_config
from voxum.orchestrator import Orchestrator
from voxum.tools import drive

logger = logging.getLogger(__name__)


def check_for_new_files() -> None:
    """Check Google Drive folder for new audio files and process them."""
    config = get_config()
    orchestrator = Orchestrator()

    logger.info("Checking for new files...")

    try:
        files = drive.list_new_files(config.google_drive_folder_id)
    except Exception as e:
        logger.error(f"Failed to list files: {e}")
        return

    new_files = [f for f in files if not drive.is_processed(f["id"])]

    if not new_files:
        logger.info("No new files found")
        return

    logger.info(f"Found {len(new_files)} new file(s)")

    for file_info in new_files:
        file_id = file_info["id"]
        filename = file_info["name"]

        logger.info(f"Processing: {filename}")

        try:
            local_path = drive.download_file(file_id, filename)

            result = orchestrator.process_file(
                file_path=local_path,
                original_filename=filename,
                drive_file_id=file_id,
            )

            if result.success:
                logger.info(f"Successfully processed: {filename}")
            else:
                logger.error(f"Failed to process {filename}: {result.error}")

            local_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error processing {filename}: {e}", exc_info=True)


def start_watcher() -> None:
    """Start the background watcher that polls Google Drive."""
    config = get_config()

    scheduler = BlockingScheduler()

    scheduler.add_job(
        check_for_new_files,
        trigger=IntervalTrigger(seconds=config.poll_interval_seconds),
        id="drive_watcher",
        name="Google Drive Watcher",
        replace_existing=True,
    )

    logger.info(
        f"Watcher started - polling every {config.poll_interval_seconds} seconds"
    )

    check_for_new_files()

    scheduler.start()
