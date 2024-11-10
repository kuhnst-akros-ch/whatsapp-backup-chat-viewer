import glob
import os
import sqlite3
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

import main
from src.logger_setup.logger_setup import LoggerSetup

# Paths
WATCH_DIR = os.getenv("MONITOR_WATCH_DIR")
# Store the cache database in a persistent Docker volume
CACHE_DB_DIR = os.getenv("MONITOR_CACHE_DB_DIR")
os.makedirs(CACHE_DB_DIR, exist_ok=True)
CACHE_DB = os.path.join(CACHE_DB_DIR, "cache.db")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")

# Lock file name
LOCK_FILENAME = os.getenv("MONITOR_LOCK_FILENAME")

log_level_monitor = os.getenv("LOG_LEVEL_MONITOR")
logger = LoggerSetup(log_level=log_level_monitor)

# Environment vars for WhatsApp extractor
OUTPUT_STYLE = os.getenv("OUTPUT_STYLE")
CONVERSATION_TYPES = set(os.getenv("CONVERSATION_TYPES", "").split(","))


def call_subprocess(file_path: str) -> bool:
    """
    Simulate the processing of a file. This function should be replaced with actual
    subprocess calls or other logic for file processing.
    Args:
        file_path (str): The path of the file to process.
    """
    dir_path = Path(file_path).parent
    try:
        # Call main.py
        main.main(
            msgdb_path=str(dir_path / "msgstore.db"),
            wadb_path=str(dir_path / "wa.db"),
            output_dir=OUTPUT_DIR,
            output_style=OUTPUT_STYLE,
            conversation_types=list(CONVERSATION_TYPES),
            phone_numbers=[]
        )
        logger.info("Completed processing file: %s", file_path)
        # todo
        raise ValueError("todo: figure out output_dir")
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
                dir_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                status TEXT CHECK(status IN ('new', 'processing', 'completed', 'error', 
                'on_hold', 'waiting'))
                    NOT NULL DEFAULT 'new',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                constraint file_cache_uq unique (dir_path, file_name)
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
    path = Path(file_path)
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.execute(
            "SELECT 1 FROM file_cache WHERE dir_path = ?  and file_name = ? LIMIT 1",
            (str(path.parent), str(path.name)))
        return cursor.fetchone() is not None


def get_waiting_files(dir_name: str) -> set[str]:
    """
    Query the file_cache table to count entries with a specific dir_path
    and file names from a provided list, using parameterized queries to prevent SQL injection.
    """
    with sqlite3.connect(CACHE_DB) as conn:
        query = '''
            SELECT      file_name
            FROM        file_cache
            WHERE       dir_path = ?
                        AND
                        status = 'waiting'
        '''
        parameters = (dir_name,)

        cursor = conn.execute(query, parameters)
        filenames = {row[0] for row in cursor.fetchall()}

    return filenames


def add_file_to_cache(file_path: str, status: str = 'new') -> None:
    """
    Add a file path to the cache with a specified status.

    Args:
        file_path (str): The path of the file to add.
        status (str): The initial status of the file.
    """
    path = Path(file_path)
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute(
            "INSERT INTO file_cache (dir_path, file_name, status) VALUES (?, ?, ?)",
            (str(path.parent), str(path.name), status))
        conn.commit()


def update_file_status(file_path: str, status: str) -> None:
    """
    Update the status of a file in the cache.

    Args:
        file_path (str): The path of the file to update.
        status (str): The new status of the file.
    """
    path = Path(file_path)
    logger.info('Updating status: %s for file %s', status, file_path)
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("UPDATE file_cache SET status = ? WHERE dir_path = ?  and file_name = ?",
                     (status, str(path.parent), str(path.name)))
        conn.commit()


def remove_file_from_cache(file_path: str) -> None:
    """
    Remove a file path from the cache.

    Args:
        file_path (str): The path of the file to remove.
    """
    path = Path(file_path)
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute("DELETE FROM file_cache WHERE dir_path = ?  and file_name = ?",
                     (str(path.parent), str(path.name)))
        conn.commit()


def _is_lock_file(file_path: str) -> bool:
    return Path(file_path).name == LOCK_FILENAME


def _are_all_files_ready(file_path) -> bool:
    dir_path = str(Path(file_path).parent)
    # todo what about lock file
    filenames = get_waiting_files(dir_path)
    # add current file, it's not waiting
    filenames.add(os.path.basename(file_path))
    if filenames == SUPPORTED_FILENAMES:
        return True
    return False


def get_current_files() -> set[str]:
    # Generate the set of current files by applying each pattern
    current_files: set[str] = set()
    for pattern in watchdir_patterns:
        current_files.update(str(f) for f in glob.glob(pattern) if os.path.isfile(f))
    return current_files


def process_file(file_path: str) -> None:
    """
    Process a file by updating its status and calling the subprocess.

    Args:
        file_path (str): The path of the file to process.
    """

    # Set status for lock-files
    if _is_lock_file(file_path):
        logger.info("Processing lock-file: %s", file_path)
        logger.info("Locking directorory: %s", os.path.dirname(file_path))
        status = 'completed'
        update_file_status(file_path, status)
    # Put files in cache as waiting until are files are present
    elif not _are_all_files_ready(file_path):
        logger.info("Caching file as 'waiting' for other files: %s", file_path)
        status = 'waiting'
        update_file_status(file_path, status)
    # Process normal files (non lock-files)
    else:
        logger.info("Processing file: %s", file_path)
        update_file_status(file_path, 'processing')
        success = call_subprocess(file_path=file_path)
        status = 'completed' if success else 'error'
        # update both db-files
        dir_path = Path(file_path)
        for filename in SUPPORTED_FILENAMES:
            update_file_status(str(dir_path / filename), status)


def process_on_hold_files_in_directory(lock_file_path: str) -> None:
    """
    Process any files that were previously on hold due to a lock file in the directory.

    Args:
        lock_file_path (Path): The directory to check for on-hold files.
    """
    # Get on-hold files from same folder from cache
    dir_path = str(Path(lock_file_path).parent)
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.execute("SELECT file_name FROM file_cache WHERE dir_path = ?  and status = ?",
                              (dir_path, 'on_hold'))
        cached_files = {row[0] for row in cursor.fetchall()}

    current_files = {f.name for f in Path(dir_path).glob('*') if f.is_file()}

    # Determine missing files (cached but not in directory)
    missing_files = set(cached_files) - current_files
    for file_name in missing_files:
        file_path = Path(dir_path) / file_name
        on_file_deleted(file_path)

    hold_files = set(cached_files) - missing_files
    for file_name in hold_files:
        file_path = Path(dir_path) / file_name
        logger.debug("Processing on-hold file: %s", file_path)
        update_file_status(str(file_path), 'new')
        process_file(file_path)


def on_file_created(file_path: str) -> None:
    # Check if the file is in the two-level folder structure
    relative_path = Path(file_path).relative_to(WATCH_DIR)
    logger.debug('New file detected: %s', relative_path)
    # Check cache
    if file_in_cache(file_path=file_path):
        logger.info('Ignoring new file (already in cache): %s', file_path)
        return

    # handle lock-file
    if _is_lock_file(file_path):
        status = 'new'
    # check lock-file exists
    elif (Path(file_path).parent / LOCK_FILENAME).exists():
        status = 'on_hold'
    else:
        status = 'new'

    # Add new file with appropriate status
    logger.info("New file detected: %s", file_path)
    add_file_to_cache(file_path=file_path, status=status)

    # Process the file immediately if no lock file is present
    if status == 'new':
        process_file(file_path=file_path)
    else:
        logger.info("File %s is on hold due to lock file", file_path)


def on_file_deleted(file_path: str) -> None:
    # Check if a lock file is removed
    if _is_lock_file(file_path):
        logger.info("Lock file removed: %s", file_path)
        # Process any files on hold in this directory
        process_on_hold_files_in_directory(file_path)
    logger.info("File deleted: %s", file_path)
    remove_file_from_cache(file_path=file_path)


# Directory event handler
class NewFileHandler(PatternMatchingEventHandler):
    def __init__(self, patterns: list[str] | None = None):
        # Pass a list of glob patterns here, e.g., ['*.txt', '*.py']
        super().__init__(patterns=patterns)

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
        on_file_created(file_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """
        Handle the event of a file being deleted from the watched directory.
        Also detects removal of lock files and triggers processing of on-hold files.

        Args:
            event (FileSystemEvent): The file system event.
        """
        if event.is_directory:
            logger.debug('Directory delete detected: %s', event.src_path)
            return
        file_path = event.src_path
        on_file_deleted(file_path)


def sync_cache_with_directory() -> None:
    """
    On startup, sync the cache with the current state of the watch directory.
    Remove any cache entries that no longer have corresponding files.
    Also handle files that may have been on hold due to lock files.
    """
    max_attempts = 10  # Set the maximum number of allowed attempts
    attempt = 0

    while attempt < max_attempts:
        # Increment attempt counter
        attempt += 1

        # Get the current list of files in the directory
        current_files: set[str] = get_current_files()

        logger.debug('Syncing cache, current files on disk: %s', current_files)

        with sqlite3.connect(CACHE_DB) as conn:
            cursor = conn.execute("SELECT dir_path, file_name, status FROM file_cache")
            cached_files = {os.path.join(row[0], row[1]): row[2] for row in cursor.fetchall()}

        # Determine missing files (in cache but not in directory)
        missing_files = set(cached_files) - current_files

        # Determine new files (in directory but not in cache)
        new_files = current_files - set(cached_files)

        # Check if there are no deltas; if so, exit the loop
        if not missing_files and not new_files:
            logger.debug("Cache synchronized with directory; no more deltas found.")
            break

        logger.info("Syncing delta between disk and cache, syncing. Attempt %d/%d",
                    attempt, max_attempts)

        # Sync
        for file_path in missing_files:
            on_file_deleted(file_path)
        for file_path in new_files:
            on_file_created(file_path)

    # Log a warning if the maximum attempts were reached
    if attempt >= max_attempts:
        logger.error("Reached maximum sync attempts (%d). Cache may still be out of sync.",
                     max_attempts)


# Directory watcher
def start_watching() -> None:
    """
    Start watching the specified directory for file changes, using polling to ensure
    compatibility across different environments.
    """
    observer = PollingObserver()
    observer.schedule(event_handler, path=WATCH_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


# Generate patterns dynamically by combining WATCH_DIR with each supported file suffix
SUPPORTED_FILENAMES = {"msgstore.db", "wa.db"}
# Add a pattern for detecting Lock.lck files
watched_filenames = SUPPORTED_FILENAMES.copy()
watched_filenames.add(LOCK_FILENAME)

watchdir_patterns = [f"{WATCH_DIR}/*/database/whatsapp/*/{filename}" for filename in watched_filenames]

logger.info("Monitoring with these patterns: %s", watchdir_patterns)

# Initialize event handler with the patterns
event_handler = NewFileHandler(patterns=watchdir_patterns)

if __name__ == "__main__":
    # Initialize cache database
    initialize_cache()

    # Sync cache with the current directory contents
    logger.info("Synchronizing cache with watch directory...")
    sync_cache_with_directory()

    # Start watching directory
    logger.info("Watching for new files in: %s", WATCH_DIR)
    start_watching()
