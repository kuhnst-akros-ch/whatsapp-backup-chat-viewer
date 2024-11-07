import os
import json
import glob
from typing import Optional, List, Dict

# Constant: Directory being watched
WATCH_DIR = "/path/to/watch/dir"

# Extract dossier and device identifiers from the current file's path
def parse_file_path(file_path: str) -> Optional[Dict[str, str]]:
    """Parse file path to extract dossier and device identifiers."""
    parts = file_path.split('/')
    try:
        dossier_id = parts[0]
        device_id = parts[3]
        return {"dossier_id": dossier_id, "device_id": device_id}
    except IndexError:
        return None

# Parse JSON metadata to extract the original filename and location
def parse_metadata_file(metadata_path: str) -> Optional[str]:
    """Extract original filename from metadata JSON file."""
    try:
        with open(metadata_path, 'r', encoding="utf-8") as file:
            metadata = json.load(file)
        return metadata.get('filename')
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Find matching files given the parsed info from current_file
def find_matching_files(current_file: str) -> List[str]:
    """Find the 4 required files based on the current file's dossier and device info."""
    file_info = parse_file_path(current_file)
    if not file_info:
        return []

    dossier_id = file_info['dossier_id']
    device_id = file_info['device_id']

    # Define glob patterns to independently search for each type of file in the expected directories
    wa_data_pattern = os.path.join(WATCH_DIR, f"{dossier_id}/database/whatsapp/{device_id}/*/*-wa.db")
    msgstore_data_pattern = os.path.join(WATCH_DIR, f"{dossier_id}/database/whatsapp/{device_id}/*/*-msgstore.db")
    wa_metadata_pattern = os.path.join(WATCH_DIR, f"{dossier_id}/database/whatsapp/{device_id}/*/metadata/*-wa.db.json")
    msgstore_metadata_pattern = os.path.join(WATCH_DIR, f"{dossier_id}/database/whatsapp/{device_id}/*/metadata/*-msgstore.db.json")

    # Locate files independently using glob
    wa_data_file = next(iter(glob.glob(wa_data_pattern)), None)
    msgstore_data_file = next(iter(glob.glob(msgstore_data_pattern)), None)
    wa_metadata_file = next(iter(glob.glob(wa_metadata_pattern)), None)
    msgstore_metadata_file = next(iter(glob.glob(msgstore_metadata_pattern)), None)

    # Ensure we have each of the required files
    if wa_data_file and msgstore_data_file and wa_metadata_file and msgstore_metadata_file:
        return [wa_data_file, wa_metadata_file, msgstore_data_file, msgstore_metadata_file]
    return []

# Main function to call on file-trigger
def monitor_file(current_file: str) -> Optional[List[str]]:
    """Triggered by a new file; checks if all required files for a dataset are present."""
    required_files = find_matching_files(current_file)
    if len(required_files) == 4:
        print("All required files found:", required_files)
        # Process the files as needed
        return required_files
    else:
        print("Incomplete set of files. Waiting for remaining files.")
    return None
