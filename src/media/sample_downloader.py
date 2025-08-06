"""
Sample audio file downloader for testing and demonstration purposes.
Provides functionality to download and cache sample audio files.
"""

import os
import requests
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Constants to replace magic numbers
SAMPLE_URL = "https://filesamples.com/samples/audio/mp3/sample3.mp3"
SAMPLES_DIR = Path("samples")
SAMPLE_FILENAME = "sample.mp3"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds
CHUNK_SIZE = 8192
PROGRESS_LOG_INTERVAL = 10  # percentage
RETRY_WAIT_MULTIPLIER = 5  # seconds
PERCENTAGE_BASE = 100  # Base for percentage calculations


def ensure_sample_file() -> str:
    """
    Ensure the sample audio file exists, downloading if necessary.

    Returns:
        str: Path to the sample audio file

    Raises:
        FileNotFoundError: If download fails after all retries
    """
    try:
        # Create samples directory if it doesn't exist
        SAMPLES_DIR.mkdir(exist_ok=True)

        # Define the local file path
        local_path = SAMPLES_DIR / SAMPLE_FILENAME

        # Download if file doesn't exist
        if not local_path.exists():
            logger.info(f"Downloading sample audio file from {SAMPLE_URL}")
            _download_sample_file(local_path)

        if not local_path.exists():
            raise FileNotFoundError("Failed to download sample file after all retries")

        return str(local_path)

    except Exception as e:
        logger.error(f"Failed to ensure sample audio file: {e}")
        raise


def _download_sample_file(local_path: Path) -> None:
    """Download the sample audio file with retry logic."""
    session = requests.Session()

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(SAMPLE_URL, stream=True, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            _save_downloaded_file(response, local_path)
            logger.info(f"Sample audio file downloaded to {local_path}")
            break  # Success, exit retry loop

        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:  # Don't sleep on the last attempt
                wait_time = (attempt + 1) * RETRY_WAIT_MULTIPLIER
                logger.warning(
                    f"Download attempt {attempt + 1} failed: {e}. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
            else:
                raise  # Re-raise the last exception if all retries failed


def _save_downloaded_file(response: requests.Response, local_path: Path) -> None:
    """Save the downloaded file with progress tracking."""
    # Get total file size if available
    total_size = int(response.headers.get("content-length", 0))

    with open(local_path, "wb") as f:
        if total_size == 0:
            # If we can't get the total size, just write the content
            f.write(response.content)
        else:
            # Download with progress tracking
            downloaded = 0
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    _log_download_progress(downloaded, total_size)


def _log_download_progress(downloaded: int, total_size: int) -> None:
    """Log download progress at regular intervals."""
    if total_size > 0:
        progress = (downloaded / total_size) * PERCENTAGE_BASE
        if int(progress) % PROGRESS_LOG_INTERVAL == 0:
            logger.info(f"Download progress: {progress:.1f}%")
