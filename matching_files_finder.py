import glob
import json
import os
from pathlib import Path
from typing import Optional, List, Dict

from src.logger_setup.logger_setup import LoggerSetup

WATCH_DIR = os.getenv("MONITOR_WATCH_DIR")

logger = LoggerSetup()


# Step 1.a: Determine if the file is a data file or a metadata file
def is_data_file(file_path: Path) -> bool:
    """Determine if the file is a data file based on its suffix."""
    return file_path.name.lower().endswith(('-wa.db', '-msgstore.db'))


# Step 1.b: Check if the counterpart file (data or metadata) exists
def find_counterpart_file(file_path: Path) -> Optional[Path]:
    """Given a data or metadata file, locate its corresponding metadata or data file."""
    # Examples:
    # data-file:        DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/FILE
    # metadata-file:    DOSSIER_ID/database/whatsapp/DEVICE_ID/12345678/metadata/FILE.json
    if is_data_file(file_path):
        # add metadata folder and .json suffix
        metadata_file = file_path.parent / 'metadata' / f"{file_path.name}.json"
        # Look for the metadata counterpart
        if os.path.exists(metadata_file):
            return metadata_file
    else:
        # This is a metadata file, so look for the data counterpart
        # remove metadata folder and .json suffix (with .stem)
        data_file = file_path.parent.parent / file_path.stem
        if os.path.exists(data_file):
            return data_file
    return None


# Step 2.a: Search for the remaining metadata files using dossier_id and device_id
def find_matching_metadata_files(dossier_id: str, device_id: str) -> List[str]:
    """Use glob to locate potential metadata files matching the dossier_id and device_id."""
    metadata_pattern = os.path.join(WATCH_DIR,
                                    f"{dossier_id}/database/whatsapp/{device_id}/*/metadata/*.json")
    return glob.glob(metadata_pattern)


# Step 2.b: Parse JSON metadata and validate based on criteria
def parse_metadata_file(metadata_path: Path) -> Optional[Dict[str, str]]:
    """Extract dossier_id, device_id, filename, and location from metadata JSON."""
    try:
        with open(metadata_path, 'r', encoding="utf8") as file:
            metadata = json.load(file)
        return {
            "dossier_id": metadata.get("dossier_id"),
            "device_id": metadata.get("device_id"),
            "filename": metadata.get("filename"),
            "location": metadata.get("location"),
        }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error('Error parsing metadata file: %s', e)
        return None


# Step 3: Main function to orchestrate the file checking and completion
def find_whatsapp_files(file_path: Path) -> Optional[Dict[str, str]]:
    """Handle a new file event and attempt to gather a complete dataset."""
    if not file_path.is_file():
        logger.error("File does not exist: %s", file_path)
        return None

    wa_file, wa_metadata, msgstore_file, msgstore_metadata = None, None, None, None

    # Step 1: Determine if file is data or metadata, and find counterpart
    if is_data_file(file_path):
        data_file = file_path
        metadata_file = find_counterpart_file(file_path)
    else:
        metadata_file = file_path
        data_file = find_counterpart_file(file_path)

    # Exit if counterpart is missing
    if not metadata_file or not data_file:
        return None

    # Step 1.b: Parse metadata to retrieve dossier_id, device_id, filename, and location
    metadata_info = parse_metadata_file(metadata_file)
    if metadata_info:
        dossier_id = metadata_info["dossier_id"]
        device_id = metadata_info["device_id"]
        location = metadata_info["location"]
        source_filename = metadata_info["filename"]
    else:
        return None

    # Assign the first pair of files (wa or msgstore based on filename)
    if source_filename == "wa.db":
        wa_file = data_file
        wa_metadata = metadata_file
    else:
        msgstore_file = data_file
        msgstore_metadata = metadata_file

    # Step 2: Find the other metadata file using glob
    matching_metadata_files = find_matching_metadata_files(dossier_id, device_id)
    other_metadata_file = None
    other_filename = "msgstore.db" if source_filename == "wa.db" else "wa.db"

    # Step 2.b: Validate each found metadata file
    for candidate_metadata_file in matching_metadata_files:
        candidate_info = parse_metadata_file(Path(candidate_metadata_file))
        if (
                candidate_info
                and candidate_info["dossier_id"] == dossier_id
                and candidate_info["device_id"] == device_id
                and candidate_info["location"] == location
                and candidate_info["filename"] == other_filename
        ):
            other_metadata_file = candidate_metadata_file
            break

    if not other_metadata_file:
        return None

    # Step 2.c: Find the corresponding data file for the other metadata file
    other_data_file = other_metadata_file[:-5]  # Remove ".json" suffix

    # Assign the other pair of files based on the filename
    if other_filename == "wa.db":
        wa_file = other_data_file
        wa_metadata = other_metadata_file
    else:
        msgstore_file = other_data_file
        msgstore_metadata = other_metadata_file

    # Step 3: Verify all files are collected
    if wa_file and wa_metadata and msgstore_file and msgstore_metadata:
        return {
            "wa_file": wa_file,
            "wa_metadata": wa_metadata,
            "msgstore_file": msgstore_file,
            "msgstore_metadata": msgstore_metadata,
        }

    return None
