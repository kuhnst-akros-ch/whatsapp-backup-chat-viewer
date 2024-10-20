from ..models import CallLog, Chat, Contact, GroupName


def chat_to_txt_raw(chat: Chat, folder: str) -> None:
    """Store chat messages in a text file without formatting.

    Args:
        chat (Chat): Chat to be formatted.
        folder (str): Directory to write the formatted chat.

    Returns:
        None: Creates .txt file of the chat in the given directory
    """

    if isinstance(chat.chat_title, Contact):
        if chat.chat_title.name and chat.chat_title.number:
            chat_title_details = f"{chat.chat_title.name} ({chat.chat_title.number})"
        elif chat.chat_title.number:
            chat_title_details = chat.chat_title.number
        else:
            chat_title_details = chat.chat_title.raw_string_jid
    elif isinstance(chat.chat_title, GroupName):
        chat_title_details = f"{chat.chat_title.name}"
    else:
        chat_title_details = ""

    messages = "\n".join([str(message) for message in chat.messages])

    file_name = chat_title_details.replace("/", "_") + "-raw.txt"
    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as file:
        file.write(f"{chat_title_details}\n\n{messages}")


def call_log_to_txt_raw(call_log: CallLog, folder: str) -> None:
    """Store call logs in a text file without formatting.

    Args:
        call_log (CallLog): CallLog to be formatted.
        folder (str): Directory to write the formatted call log.

    Returns:
        None: Creates .txt file of the call log in the given directory.
    """
    if call_log.caller_id.name and call_log.caller_id.number:
        caller_id_details = f"{call_log.caller_id.name} ({call_log.caller_id.number})"
    elif call_log.caller_id.number:
        caller_id_details = call_log.caller_id.number
    else:
        caller_id_details = call_log.caller_id.raw_string_jid

    call_logs = "\n".join([str(call) for call in call_log.calls])

    file_name = caller_id_details.replace("/", "_") + "-raw.txt"
    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as file:
        file.write(f"{caller_id_details}\n\n{call_logs}")
