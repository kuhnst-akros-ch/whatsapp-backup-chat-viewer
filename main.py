import argparse
import os
import sqlite3
from typing import List, Generator, Tuple, Dict

from tqdm import tqdm

from src.call_log_extractor import builder as call_log_builder
from src.chat_extractor import builder as chat_builder
from src.contact_extractor import builder as contact_builder
from src.exports.call_log_to_txt_formatted import call_log_to_txt_formatted
from src.exports.chat_to_txt_formatted import chat_to_txt_formatted
from src.exports.contacts_to_txt_formatted import contacts_to_txt_formatted
from src.exports.to_json import call_log_to_json, chat_to_json
from src.exports.to_txt_raw import call_log_to_txt_raw, chat_to_txt_raw
from src.models import Chat, CallLog, Contact

CALL_LOGS_DIR = "/call_logs"
CHAT_DIR = "/chats"
CONTACTS_FIlE = "/contacts.txt"


def create_db_connection(file_path: str) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Create a database connection and return it.

    The function takes a single argument, `file_path`, which is a string. The function returns a tuple
    of two items: a `sqlite3.Connection` object and a `sqlite3.Cursor` object

    Args:
      file_path (str): The path to the database file.

    Returns:
      A tuple of the connection and cursor objects.
    """
    db = sqlite3.connect(f'file:{file_path}?mode=ro', uri=True)
    return db, db.cursor()


def close_db_connections(databases: List[sqlite3.Connection]) -> None:
    """Close all the database connections in the list of database connections.

    The function takes a list of database connections and closes them all.

    Args:
      databases (List[sqlite3.Connection]): A list of sqlite3.Connection objects.
    """
    for db in databases:
        db.close()


def load_call_logs(
        msgdb_cursor: sqlite3.Cursor,
        output_call_logs_directory: str,
        phone_numbers: List[str],
        contacts: Dict[str, List[Contact]]
) -> [Generator[CallLog, None, None]]:
    if not os.path.exists(output_call_logs_directory):
        os.makedirs(output_call_logs_directory)
    if not phone_numbers:
        return call_log_builder.build_all_call_logs(msgdb_cursor, contacts)
    else:
        return [
            call_log_builder.build_call_log_for_given_id_or_phone_number(
                msgdb_cursor, contacts, phone_number=phone_number
            ) for phone_number in phone_numbers
        ]


def load_chats(
        msgdb_cursor: sqlite3.Cursor,
        output_chat_directory: str,
        phone_numbers: List[str],
        contacts: Dict[str, List[Contact]]
) -> [Generator[Chat, None, None]]:
    if not os.path.exists(output_chat_directory):
        os.makedirs(output_chat_directory)
    if not phone_numbers:
        return chat_builder.build_all_chats(msgdb_cursor, contacts)
    else:
        return [
            chat_builder.build_chat_for_given_id_or_phone_number(
                msgdb_cursor, contacts, phone_number=phone_number
            ) for phone_number in phone_numbers
        ]


def export_call_log(call_log: CallLog, folder: str, output_style: str) -> None:
    if call_log.calls:
        if output_style == "raw_txt":
            call_log_to_txt_raw(call_log=call_log, folder=folder)
        elif output_style == "formatted_txt":
            call_log_to_txt_formatted(call_log=call_log, folder=folder)
        elif output_style == "json":
            call_log_to_json(call_log=call_log, folder=folder)
        else:
            raise AssertionError("Invalid 'call_log formatting' requested")


def export_chat(chat: Chat, folder: str, output_style: str) -> None:
    if output_style == "raw_txt":
        chat_to_txt_raw(chat=chat, folder=folder)
    elif output_style == "formatted_txt":
        chat_to_txt_formatted(chat=chat, folder=folder)
    elif output_style == "json":
        chat_to_json(chat=chat, folder=folder)
    else:
        raise AssertionError("Invalid 'chat formatting' requested")


def main(
        msgdb_path: str,
        wadb_path: str,
        output_dir: str,
        conversation_types: List[str],
        phone_numbers: List[str],
        output_style: str
) -> None:
    if output_style not in ("raw_txt", "formatted_txt", "json"):
        raise AssertionError(f"Invalid formatting '{args.output_style}' requested")

    wadb, wadb_cursor = create_db_connection(wadb_path)
    try:
        contacts = contact_builder.build_all_contacts(wadb_cursor)
    finally:
        close_db_connections([wadb])

    msgdb, msgdb_cursor = create_db_connection(msgdb_path)
    try:
        output_call_logs_directory = output_dir + CALL_LOGS_DIR
        output_chat_directory = output_dir + CHAT_DIR
        output_contacts_file = output_dir + CONTACTS_FIlE

        if "call_logs" in conversation_types:
            call_logs = load_call_logs(msgdb_cursor, output_call_logs_directory, phone_numbers, contacts)
            for call_log in tqdm(call_logs):
                export_call_log(call_log=call_log, folder=output_call_logs_directory, output_style=output_style)

        if "chats" in conversation_types:
            chats = load_chats(msgdb_cursor, output_chat_directory, phone_numbers, contacts)
            for chat in tqdm(chats):
                export_chat(chat=chat, folder=output_chat_directory, output_style=output_style)

        if "contacts" in conversation_types:
            contacts_to_txt_formatted(contacts=contacts, file_name=output_contacts_file)

    finally:
        close_db_connections([msgdb])


if __name__ == "__main__":

    ap = argparse.ArgumentParser(
        description="Project to extract Whatsapp conversations and/or call logs from the app's SQLite database and exporting them as JSON or TXT files."
    )
    ap.add_argument(
        "--msgdb", "-mdb", type=str, required=True, help="Path to 'msgstore.db' file"
    )
    ap.add_argument(
        "--wadb", "-wdb", type=str, required=True, help="Path to 'wa.db' file"
    )
    ap.add_argument(
        "--conversation_types",
        "-t",
        choices=["call_logs", "chats", "contacts"],
        nargs="+",
        type=str,
        default=["call_logs", "chats", "contacts"],
        help="Backup only call_logs, only chats, or both (by providing both)",
    )
    ap.add_argument(
        "--output_style",
        "-s",
        choices=["raw_txt", "formatted_txt", "json"],
        type=str,
        default="formatted_txt",
        help="Style in which your parsed backup will be stored",
    )
    ap.add_argument(
        "--output_dir",
        "-o",
        type=str,
        help="Path to directory where your parsed chats and/or parsed call logs will be stored",
    )
    ap.add_argument(
        "--phone_number_filter",
        "-f",
        nargs="*",
        default=[],
        help="Phone numbers (format: XXXXXXXXXXXX) of the chats and/or call logs that you want to extract from the database. Empty means all phone numbers",
    )
    args = ap.parse_args()

    main(
        msgdb_path=args.msgdb,
        wadb_path=args.wadb,
        output_dir=args.output_dir,
        conversation_types=args.conversation_types,
        phone_numbers=args.phone_number_filter,
        output_style=args.output_style
    )
