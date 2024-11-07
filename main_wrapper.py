import fnmatch
import os
from pathlib import Path

from src.logger_setup.logger_setup import LoggerSetup

# Call the script with the provided paths
# command = [
#               "python", "main.py",
#               "--msgdb", request.json.get('msgdb'),
#               "--wadb", request.json.get('wadb'),
#               "--output_style", request.json.get('output_style', 'formatted_txt'),
#               "--output_dir", request.json.get('output_dir'),
#               "--conversation_types"
#           ] + request.json.get('conversation_types', ['call_logs', 'chats', 'contacts'])

# Paths
WATCH_DIR_ENV = os.getenv("MONITOR_WATCH_DIR")
WATCH_DIR = Path(WATCH_DIR_ENV)
# globs
FILTER_PATTERN_FILE = os.getenv("MONITOR_FILTER_PATTERN_FILE")
FILTER_PATTERN_METADATA = os.getenv("MONITOR_FILTER_PATTERN_METADATA")

logger = LoggerSetup()


def main(file_path: Path) -> None:
    # todo
    logger.info('Received new file_path: %s', file_path)

    # relative path should be like:
    # DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/FILE
    # or for metadata json
    # DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/metadata/FILE.json
    # where FILE is either '*-msgstore.db' or '*-wa.db' (case-insensitive)
    relative_path = file_path.relative_to(WATCH_DIR)

    matches, patterns = check_pattern_case_insensitive(relative_path)
    if not matches:
        logger.debug("File %s filtered out, it does not match any pattern of %s ", file_path,
                     patterns)
        return


def check_pattern_case_insensitive(relative_path) -> [bool, list[str]]:
    # check case-insensitive
    patterns = [
        f"{FILTER_PATTERN_FILE}-msgstore.db",
        f"{FILTER_PATTERN_METADATA}-msgstore.db.json",
        f"{FILTER_PATTERN_FILE}-wa.db",
        f"{FILTER_PATTERN_METADATA}-wa.db.json"
    ]
    matches = any(fnmatch.fnmatch(str(relative_path).lower(), pattern) for pattern in patterns)
    return matches, patterns


def get_glob_pattern(
        relative_path: Path,
        pattern: str
) -> str:
    parts = list(relative_path.parts)
    pattern_parts = list(Path(pattern).parts)
    # dossier_id
    pattern_parts[0] = parts[0]
    # device_id
    pattern_parts[3] = parts[3]
    path = Path(*pattern_parts)
    return str(path)


def get_file_candidates(relative_path: Path) -> None:

    pattern_file = get_glob_pattern(relative_path, FILTER_PATTERN_FILE)
    matching_files = list(WATCH_DIR.glob(pattern_file))

    # filter case-insensitive
    matching_msgstore = [s for s in matching_files if s.lower().endswith('-msgstore.db')]
    matching_wa = [s for s in matching_files if s.lower().endswith('-wa.db')]

    if not matching_msgstore or not matching_wa:
        logger.debug('Did not find msgstore.db and wa.db files')
        return None

    pattern_metadata = get_glob_pattern(relative_path, FILTER_PATTERN_METADATA)
    matching_metadata = list(WATCH_DIR.glob(pattern_metadata))

    # filter case-insensitive
    matching_metadata_msgstore = [s for s in matching_metadata if s.lower().endswith('-msgstore.db.json')]
    matching_metadata_wa = [s for s in matching_metadata if s.lower().endswith('-wa.db.json')]

    if not matching_metadata_msgstore or not matching_metadata_wa:
        logger.debug('Did not find msgstore.db.json and wa.db.json files')
        return None

    file_msgstore = file_wa = metadata_msgstore = metadata_wa = None

    # find current file
    if relative_path in matching_msgstore:
        logger.debug('Found msgstore.db: %s', relative_path)
        file_msgstore = relative_path
    elif relative_path in matching_wa:
        logger.debug('Found wa.db: %s', relative_path)
        file_wa = relative_path
    elif relative_path in matching_metadata_msgstore:
        logger.debug('Found msgstore.db.json: %s', relative_path)
        metadata_msgstore = relative_path
    elif relative_path in matching_metadata_wa:
        logger.debug('Found wa.db.json: %s', relative_path)
        metadata_wa = relative_path
    else:
        logger.error('Relative path does not match any pattern. This should not happen here! %s', relative_path)
        return None

    if relative_path in matching_files:
        logger.debug('Found file %s', relative_path)
        matching_files.remove(relative_path)
        if relative_path.name.lower().endswith('-msgstore.db'):
            file_msgstore = relative_path
        elif relative_path.name.lower().endswith('-wa.db'):
            file_wa = relative_path
        else:
            logger.warning("Filtering out file (this should have been filtered out already): %s", relative_path)
            return None
    elif relative_path in matching_metadata:
        logger.debug('Found metadata %s', relative_path)
        matching_metadata.remove(relative_path)
        if relative_path.name.lower().endswith('-msgstore.db.json'):
            metadata_msgstore = relative_path
        elif relative_path.name.lower().endswith('-wa.db.json'):
            metadata_wa = relative_path
        else:
            logger.warning("Filtering out metadata file (this should have been filtered out already): %s", relative_path)
            return None
    else:
        logger.error('Relative path does not match any pattern. This should not happen here! %s', relative_path)
        return None



        # [file for pattern in patterns for file in WATCH_DIR.glob(pattern)]

    # match = False
    # if len(suffixes) == 1 and suffixes[0].lower() == '.db':
    #     match = True
    # elif len(suffixes) == 2 and ''.join(suffixes).lower() == '.db.json':
    #     # todo
    #     pass
    #
    # # Ensure exactly two folders deep in Dossier/Device structure
    # if len(relative_path.parts) != 3:
    #     logger.info('Ignoring new file (not in Dossier/Device structure): %s', file_path)
    #     return
