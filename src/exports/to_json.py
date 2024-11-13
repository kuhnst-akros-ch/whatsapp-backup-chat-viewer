import json
import os

from attrs import asdict

from ..common import contact_to_str
from ..models import CallLog, Chat, Contact, GroupName


def chat_to_json(chat: Chat, folder: str) -> str:
    """Store chat as a JSON file.

    It takes a chat object and a directory, and writes a json file to the directory with the chat's
    title as the file name

    Args:
        chat (Chat): Chat - the chat object to be converted to JSON
        folder (str): The directory to save the chats to.

    Returns:
        None: Creates .json file of the chat in the given directory
    """
    if isinstance(chat.chat_title, Contact):
        chat_title_details = contact_to_str(chat.chat_title)
    elif isinstance(chat.chat_title, GroupName):
        chat_title_details = f"{chat.chat_title.name}"
    else:
        chat_title_details = ""

    file_name = chat_title_details.replace("/", "_") + ".json"
    file_path = os.path.join(folder, file_name)
    with open(file_path, "w", encoding="utf8") as file:
        json.dump(asdict(chat), file, sort_keys=True, indent=4, ensure_ascii=False)
    return file_path


def call_log_to_json(call_log: CallLog, folder: str) -> str:
    """Store call logs as a JSON file.

    It takes a `CallLog` object and a directory path, and writes a JSON file to the directory with the
    name of the caller ID details

    Args:
        call_log (CallLog): CallLog - The call log object to be converted to JSON.
        folder (str): The directory where the JSON files will be saved.

    Returns:
        None: Creates .json file of the chat in the given directory
    """
    caller_id_details = contact_to_str(call_log.caller_id)

    file_name = caller_id_details.replace("/", "_") + ".json"
    file_path = os.path.join(folder, file_name)
    with open(file_path, "w", encoding="utf8") as file:
        json.dump(asdict(call_log), file, sort_keys=True, indent=4, ensure_ascii=False)
    return file_path
