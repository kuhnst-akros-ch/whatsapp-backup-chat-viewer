import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.logger_setup.logger_setup import LoggerSetup

logger = LoggerSetup()


# Data class to encapsulate the context
@dataclass
class MetadataContext:
    output_dir: Path
    dossier_id: str
    device_id: str
    msgdb_path: str
    wadb_path: str


def write_metadata(
        msgdb_cursor: sqlite3.Cursor,
        context: MetadataContext,
        exported_file_path: str,
        chat_row_id: Optional[int]
) -> None:
    """
    Writes metadata to a JSON file and logs the success or failure.
    """
    exported_folder = os.path.dirname(exported_file_path)
    exported_filename = os.path.basename(exported_file_path)
    # Create metadata JSON
    metadata = {
        # Structured data
        "dossier_id": context.dossier_id,
        "device_id": context.device_id
    }
    # Add media and locations for chats
    if chat_row_id:
        metadata["properties"] = {}
        media = _get_media(msgdb_cursor, chat_row_id)
        if media:
            metadata["properties"]["media"] = media
        locations = _get_locations(msgdb_cursor, chat_row_id)
        if locations:
            metadata["properties"]["locations"] = locations
        # Remove 'properties' if it's empty
        if not metadata["properties"]:
            del metadata["properties"]
    # Define output file and path
    metadata_folder = os.path.join(exported_folder, "metadata")
    metadata_path = os.path.join(metadata_folder, f"{exported_filename}.json")
    # create metadata folder
    os.makedirs(metadata_folder, exist_ok=True)
    try:
        with open(metadata_path, "w", encoding="utf-8") as meta_file:
            # Use this for debugging:
            # json.dump(metadata, meta_file, ensure_ascii=False, indent=4)
            # Print compact json
            json.dump(metadata, meta_file, ensure_ascii=False, separators=(',', ':'))
        logger.debug("Metadata file %s created for file: %s", metadata_path, exported_file_path)
    except Exception as exc:
        logger.error("Error creating metadata %s file for file %s: %s",
                     metadata_path, exported_file_path, exc)


def _convert_to_datetime(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if ts else None


def _get_media(msgdb_cursor: sqlite3.Cursor, chat_row_id: int) -> List[Dict[str, Any]] | None:
    query = """
        SELECT      '/storage/emulated/0/WhatsApp/' || file_path file_path,
                    '/data/data/com.whatsapp/files' || direct_path direct_path,
                    mime_type,
                    file_length
        FROM        message_media
        WHERE       chat_row_id=?
    """
    return _query_to_array_of_dict(chat_row_id, msgdb_cursor, query)


def _get_locations(msgdb_cursor: sqlite3.Cursor, chat_row_id: int) -> List[Dict[str, Any]] | None:
    query = """
        SELECT		latitude,
                    longitude,
                    place_name,
                    place_address,
                    url,
                    live_location_share_duration,
                    live_location_final_latitude,
                    live_location_final_longitude,
                    live_location_final_timestamp
        FROM		message_location
        WHERE		chat_row_id = ?
    """
    return _query_to_array_of_dict(chat_row_id, msgdb_cursor, query)


def _query_to_array_of_dict(chat_row_id, msgdb_cursor, query) -> List[Dict[str, Any]] | None:
    execution = msgdb_cursor.execute(query, (chat_row_id,))
    rows = execution.fetchall()  # Fetch all rows
    # Get column names from the cursor's description
    columns = [col[0] for col in execution.description]
    # Build an array of dictionaries, excluding None values
    result = [
        {col: value for col, value in zip(columns, row) if value is not None}
        for row in rows
    ]
    return result if result else None
