from datetime import datetime, timezone
from typing import Callable, List, Generator

from src.common import contact_to_str, contact_to_full_str
from src.models import Chat, Message, Contact, GroupName


def chat_to_txt_formatted(chat: Chat, folder: str) -> None:
    """Format chat messages in a readable format and store them as a text file.

    Args:
        chat (Chat): Chat to be formatted.
        folder (str): Directory to write the formatted chat.

    Returns:
        None: Creates .txt file of the chat in the given directory
    """
    message_list = []

    for idx, message in enumerate(chat.messages):
        if (
            not message.text_data
            and not message.reply_to
            and not message.media
            and not message.geo_position
        ):
            # If there is no data or media or reply_to, we can assume that the message was about change in chat settings.
            date_time = datetime.fromtimestamp(int(message.timestamp) / 1000, timezone.utc)
            message_str = f"[{date_time}] 'Change in the chat settings'"
        else:
            message_str = get_message_str(chat, idx, message)

        message_list.append(message_str)

    chat_title_details = get_chat_title_details(chat)

    # list all participants
    participants_details = get_chat_participants_details(chat)

    # prepend group-name
    if isinstance(chat.chat_title, GroupName):
        participants_details = chat_title_details + '\n' + get_chat_participants_details(chat)

    messages = "\n".join(message_list)

    file_name = chat_title_details.replace("/", "_") + ".txt"
    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as file:
        file.write(f"{participants_details}\n\n{messages}")


def get_message_str(chat, idx, message) -> str:
    date_time = datetime.fromtimestamp(int(message.timestamp) / 1000, timezone.utc)
    sender_name = resolve_sender_name(msg=message)
    message_str = (
        f"[{date_time}]: {sender_name} - {message.text_data}"
        if message.text_data
        else f"[{date_time}]: {sender_name}"
    )
    # Retrieve the 'original message' to which the replied message belongs to.
    if message.reply_to:
        orig_message = next(
            find_reply(
                lambda x, msg=message: msg.reply_to == x.key_id,
                chat.messages[:idx],
            ),
            None,
        )  # Get the original message.
        message_str += get_orig_message_str(orig_message)
    # Retrieve media from the message if any
    if message.media:
        message_str += f"\n\t>>> Media: {message.media.file_path}"
    # Retrieve location from the message if any
    if message.geo_position:
        message_str += f"\n\t>>> Location: ({message.geo_position.latitude},{message.geo_position.longitude})"
    return message_str


def get_orig_message_str(orig_message: Message) -> str:
    # Check if the reply is given to a deleted message
    # If orig_message is None, we can assume that the original message was deleted
    if orig_message:
        if orig_message.text_data:
            orig_message_data_str = " ".join(
                orig_message.text_data.splitlines()
            )
        elif orig_message.media:
            orig_message_data_str = f"media: {orig_message.media.file_path}"
        elif orig_message.geo_position:
            orig_message_data_str = f"location: ({orig_message.geo_position.latitude},{orig_message.geo_position.longitude})"
        else:
            orig_message_data_str = ""
        return f"\n\t>>> Reply to: {resolve_sender_name(orig_message)} - {orig_message_data_str}"
    else:
        return "\n\t>>> Reply to: 'Message has been deleted'"


def find_reply(
    compare_function: Callable, chat_list: List[Message]
) -> Generator[Message, None, None]:
    """Generator function to find the message to which a reply was given.

    Args:
        compare_function (function): Compare lambda function that needs to be run against the chat_list.
        chat_list (List[Message]): List of chat messages.

    Yields:
        Message: Message object to which the reply was given.
    """
    for ct in chat_list:
        if compare_function(ct):
            yield ct


def resolve_sender_name(msg: Message) -> str:
    """Utility function to extract 'sender_name' from a given message.

    Args:
        msg (Message): Message from which we want to extract sender_name.

    Returns:
        str: sender_name
    """
    if msg.from_me:
        return "Me"
    else:
        return contact_to_str(msg.sender_contact)


def get_chat_title_details(chat: Chat) -> str:
    if isinstance(chat.chat_title, Contact):
        chat_title_details = contact_to_str(chat.chat_title)
    elif isinstance(chat.chat_title, GroupName):
        chat_title_details = f"{chat.chat_title.name}"
    else:
        chat_title_details = ""
    return chat_title_details


def get_chat_participants_details(chat: Chat) -> str:
    if not chat.participants:
        return ""
    contacts_str = [contact_to_full_str(contact) for contact in chat.participants]
    contacts_str.sort()
    return '\n'.join(contacts_str)
