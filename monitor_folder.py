import os
import sqlite3
import time
from pathlib import Path
from typing import Set

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

import main_wrapper
from src.logger_setup.logger_setup import LoggerSetup

# Paths
WATCH_DIR = os.getenv("MONITOR_WATCH_DIR")
# Store the cache database in a persistent Docker volume
CACHE_DB_DIR = os.getenv("MONITOR_CACHE_DB_DIR")
os.makedirs(CACHE_DB_DIR, exist_ok=True)
CACHE_DB = os.path.join(CACHE_DB_DIR, "cache.db")

log_level_monitor = os.getenv("LOG_LEVEL_MONITOR")
logger = LoggerSetup(log_level=log_level_monitor)

# relative path should be like:
# DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/FILE
# or for metadata json
# DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/metadata/FILE.json
FILTER_PATTERN_FILE = os.getenv("MONITOR_FILTER_PATTERN_FILE")
FILTER_PATTERN_METADATA = os.getenv("MONITOR_FILTER_PATTERN_METADATA")

def call_subprocess(file_path: str) -> bool:
    """
    Simulate the processing of a file. This function should be replaced with actual
    subprocess calls or other logic for file processing.
    Args:
        file_path (str): The path of the file to process.
    """
    try:
        # Call main_wrapper.py
        main_wrapper.main(Path(file_path))
        logger.info("Completed processing file: %s", file_path)
        return True
    except Exception as e:
        logger.error("Could not process file: %s: %s", file_path, e)
        return False


# Database setup
def initialize_cache() -> None:
    """
    Initialize the SQLite cache database, creating a table to track file paths
    and processing statuses if it does not already exist.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS file_cache (
                id INTEGER PRIMARY KEY,
                file_path TEXT UNIQUE NOT NULL,
                status TEXT CHECK(status IN ('new', 'processing', 'completed', 'error'))
                    NOT NULL DEFAULT 'new',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


def file_in_cache(file_path: str) -> bool:
    """
    Check if a file is already in the cache.

    Args:
        file_path (str): The path of the file to check.

    Returns:
        bool: True if the file is in the cache, False otherwise.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.execute("SELECT 1 FROM file_cache WHERE file_path = ? LIMIT 1", (file_path,))
        return cursor.fetchone() is not None


def add_file_to_cache(file_path: str) -> None:
    """
    Add a file path to the cache.

    Args:
        file_path (str): The path of the file to add.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("INSERT OR IGNORE INTO file_cache (file_path) VALUES (?)", (file_path,))
        conn.commit()


def remove_file_from_cache(file_path: str) -> None:
    """
    Remove a file path from the cache.

    Args:
        file_path (str): The path of the file to remove.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        conn.commit()


# Directory event handler
class NewFileHandler(PatternMatchingEventHandler):
    def __init__(self):
        pattern_file = Path(WATCH_DIR) / FILTER_PATTERN_FILE
        pattern_metadata = Path(WATCH_DIR) / FILTER_PATTERN_METADATA
        super().__init__(patterns=[str(pattern_file), str(pattern_metadata)])

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle the event of a file being created in the watched directory.

        Args:
            event (FileSystemEvent): The file system event.
        """
        if event.is_directory:
            logger.debug('New directory detected: %s', event.src_path)
            return
        file_path = event.src_path
        self.on_file_created(file_path)

    def on_file_created(self, file_path: str) -> None:
        logger.debug('New file detected %s', file_path)
        # Check cache
        if file_in_cache(file_path=file_path):
            logger.info('Ignoring new file (already in cache): %s', file_path)
            return
        # Add new file
        logger.info("New file detected: %s", file_path)
        add_file_to_cache(file_path=file_path)
        self.process_file(file_path=file_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """
        Handle the event of a file being deleted from the watched directory.

        Args:
            event (FileSystemEvent): The file system event.
        """
        if event.is_directory:
            logger.debug('Directory delete detected: %s', event.src_path)
            return
        file_path = event.src_path
        logger.info("File deleted: %s", file_path)
        remove_file_from_cache(file_path=file_path)

    @staticmethod
    def process_file(file_path: str) -> None:
        logger.info("Processing file: %s", file_path)
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
            UPDATE file_cache 
            SET status = 'processing' 
            WHERE file_path = ?""", (file_path,))
            conn.commit()

        # call subprocess
        success = call_subprocess(file_path=file_path)

        # Determine final status based on exit code
        final_status = 'completed' if success else 'error'

        logger.debug('Writing final status: %s for file %s', final_status, file_path)
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("""
            UPDATE file_cache 
            SET status = ? 
            WHERE file_path = ?""", (final_status, file_path))
            conn.commit()


def sync_cache_with_directory() -> None:
    """
    On startup, sync the cache with the current state of the watch directory.
    Remove any cache entries that no longer have corresponding files.
    """
    # Find all files in the expected two-level folder structure
    current_files: Set[str] = {str(f) for f in Path(WATCH_DIR).rglob("*") if
                               f.is_file() and len(f.relative_to(WATCH_DIR).parts) == 3}
    logger.debug('Syncing cache, current files on disk: %s', current_files)
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.execute("SELECT file_path FROM file_cache")
        cached_files: Set[str] = {row[0] for row in cursor.fetchall()}

        # Determine missing files (cached but not in directory)
        missing_files = cached_files - current_files

        # Remove missing files from the cache
        for file_path in missing_files:
            logger.info("Removing stale cache entry for missing file: %s", file_path)
            remove_file_from_cache(file_path=file_path)

        # Determine new files (not in cache)
        new_files = current_files - cached_files

        # Process new files
        for file_path in new_files:
            logger.info("Adding new cache entry for file: %s", file_path)
            event_handler.on_file_created(file_path)


# Directory watcher
def start_watching() -> None:
    """
    Start watching the specified directory for file changes, using polling to ensure
    compatibility across different environments.
    """
    observer = PollingObserver()  # Force watchdog to use polling
    observer.schedule(event_handler, path=WATCH_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


event_handler = NewFileHandler()

if __name__ == "__main__":
    # Initialize cache database
    initialize_cache()

    # Sync cache with the current directory contents
    logger.info("Synchronizing cache with watch directory...")
    sync_cache_with_directory()

    # Start watching directory
    logger.info("Watching for new files in: %s", WATCH_DIR)
    start_watching()
