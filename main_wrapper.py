import os
from pathlib import Path

import main
from matching_files_finder import find_whatsapp_files
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

logger = LoggerSetup()


def wrap_main(file_path: Path) -> None:
    logger.info('Received new file_path: %s', file_path)
    whatsapp_files = find_whatsapp_files(file_path)
    main.main(
        msgdb_path=whatsapp_files.msgstore_file,
        wadb_path=whatsapp_files.wa_file,
        output_dir='/data/output',
        conversation_types=["call_logs", "chats", "contacts"],
        phone_numbers=[],
        output_style='formatted_txt'
    )
