import os
import json
import glob
from typing import Optional, List, Dict

WATCH_DIR = "/path/to/watch/dir"

# Step 1.a: Determine if the file is a data file or a metadata file
def is_data_file(file_path: str) -> bool:
    """Determine if the file is a data file based on its suffix."""
    return file_path.lower().endswith(('-wa.db', '-msgstore.db'))

# Step 1.b: Check if the counterpart file (data or metadata) exists
def find_counterpart_file(file_path: str) -> Optional[str]:
    """Given a data or metadata file, locate its corresponding metadata or data file."""
    if is_data_file(file_path):
        # Look for the metadata counterpart
        metadata_file = file_path + ".json"
        if os.path.exists(metadata_file):
            return metadata_file
    else:
        # This is a metadata file, so look for the data counterpart
        data_file = file_path[:-5]  # Remove '.json' suffix to get the data file path
        if os.path.exists(data_file):
            return data_file
    return None

# Step 2.a: Search for the remaining metadata files using dossier_id and device_id
def find_matching_metadata_files(dossier_id: str, device_id: str) -> List[str]:
    """Use glob to locate potential metadata files matching the dossier_id and device_id."""
    metadata_pattern = os.path.join(WATCH_DIR, f"{dossier_id}/database/whatsapp/{device_id}/*/metadata/*.json")
    return glob.glob(metadata_pattern)

# Step 2.b: Parse JSON metadata and validate based on criteria
def parse_metadata_file(metadata_path: str) -> Optional[Dict[str, str]]:
    """Extract dossier_id, device_id, filename, and location from metadata JSON."""
    try:
        with open(metadata_path, 'r') as file:
            metadata = json.load(file)
        return {
            "dossier_id": metadata.get("dossier_id"),
            "device_id": metadata.get("device_id"),
            "filename": metadata.get("filename"),
            "location": metadata.get("location"),
        }
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# Step 3: Main function to orchestrate the file checking and completion
def monitor_file(file_path: str) -> Optional[List[str]]:
    """Handle a new file event and attempt to gather a complete dataset."""
    if not os.path.exists(file_path):
        print("File does not exist.")
        return None

    dossier_id, device_id = None, None
    metadata_file, data_file = None, None

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

    # Step 1.b: Extract dossier_id and device_id from the metadata file
    metadata_info = parse_metadata_file(metadata_file)
    if metadata_info:
        dossier_id = metadata_info["dossier_id"]
        device_id = metadata_info["device_id"]
        location = metadata_info["location"]
        base_filename = metadata_info["filename"]
    else:
        return None

    # Step 2: Find the other metadata file using glob
    matching_metadata_files = find_matching_metadata_files(dossier_id, device_id)
    other_metadata_file = None
    other_filename = "msgstore.db" if base_filename == "wa.db" else "wa.db"

    # Step 2.b: Validate each found metadata file
    for candidate_metadata_file in matching_metadata_files:
        candidate_info = parse_metadata_file(candidate_metadata_file)
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

    # Step 2.c: With the path of the other metadata file, find the corresponding data file
    other_data_file = other_metadata_file[:-5]  # Remove ".json" suffix

    # Step 3: Verify all files are collected
    if all([data_file, metadata_file, other_data_file, other_metadata_file]):
        return [data_file, metadata_file, other_data_file, other_metadata_file]

    return None
