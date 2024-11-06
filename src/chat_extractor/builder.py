import sqlite3
from itertools import chain
from typing import Generator, Union, Dict, List

from ..common import contact_resolver
from ..models import Chat, Contact, GeoPosition, GroupName, Media, Message
from .resolver import (
    chat_resolver,
    geo_position_resolver,
    media_resolver,
    message_resolver, group_chat_participant_jid_resolver,
)


def build_message_for_given_id(
    msgdb_cursor: sqlite3.Cursor, contacts: Dict[str, List[Contact]], message_id: int
) -> Message:
    """Extract text message, media (if available) and location (if available) for a given message_id.

    It takes a message id, and returns a Message object

    Args:
        msgdb_cursor (sqlite3.Cursor): The cursor for the 'msgdb' database.
        contacts (Dict[str, List[Contact]]): Dict of all contacts and jid as key.
        message_id (int): The message id of the message you want to extract.

    Returns:
        A Message object corresponding to the given message_id.
    """
    message, raw_string_jid = message_resolver(
        msgdb_cursor=msgdb_cursor, message_row_id=message_id
    )

    if raw_string_jid:
        message["sender_contact"] = contact_resolver(contacts=contacts, raw_string_jid=raw_string_jid)
    else:
        message["sender_contact"] = None

    media = media_resolver(msgdb_cursor=msgdb_cursor, message_row_id=message_id)
    if media:
        message["media"] = Media(**media)
    else:
        message["media"] = None

    geo_position = geo_position_resolver(
        msgdb_cursor=msgdb_cursor, message_row_id=message_id
    )
    if geo_position:
        message["geo_position"] = GeoPosition(**geo_position)
    else:
        message["geo_position"] = None

    return Message(**message)


def build_chat_for_given_id_or_phone_number(
    msgdb_cursor: sqlite3.Cursor,
    contacts: Dict[str, List[Contact]],
    chat_row_id: int = None,
    phone_number: str = None,
) -> Union[Chat, None]:
    """Extract all the messages and media (if available) for a given chat_row_id or phone_number.

    It takes a chat_row_id or phone_number and returns a Chat object.

    Args:
        msgdb_cursor (sqlite3.Cursor): The cursor for the 'msgdb' database.
        contacts (Dict[str, List[Contact]]): Dict of all contacts and jid as key.
        chat_row_id (int): ID of the chat to extract. Defaults to None.
        phone_number (str): Phone Number of the person you want to extract the chats of. Defaults to None.

    Returns:
        Chat: Chat corresponding to the given chat_row_id or phone_number.
    """
    if chat_row_id:
        chat, raw_string_jid = chat_resolver(
            msgdb_cursor=msgdb_cursor, chat_row_id=chat_row_id
        )
    elif phone_number:
        chat, raw_string_jid = chat_resolver(
            msgdb_cursor=msgdb_cursor, phone_number=phone_number
        )
    else:
        raise AssertionError("'chat_row_id' and 'phone_number' both cannot be None")

    contact = contact_resolver(contacts=contacts, raw_string_jid=raw_string_jid)
    if contact.name and not contact.number:
        chat["chat_title"] = GroupName(raw_string_jid=raw_string_jid, name=contact.name)
    else:
        chat["chat_title"] = contact

    query = "SELECT message._id FROM 'message' WHERE message.chat_row_id=?"
    execution = msgdb_cursor.execute(query, (chat.get("chat_id"),))
    res_query = list(chain.from_iterable(execution.fetchall()))
    chat["messages"] = [
        build_message_for_given_id(msgdb_cursor, contacts, message_id)
        for message_id in res_query
    ]

    chat_participant_jids = group_chat_participant_jid_resolver(msgdb_cursor=msgdb_cursor, chat_jid_raw_string=raw_string_jid)
    # add contacts from messages
    for message in chat['messages']:
        if not message.from_me and message.sender_contact:
            chat_participant_jids.append(message.sender_contact.raw_string_jid)
    # unique participants
    chat['participants'] = [contact_resolver(contacts, jid) for jid in set(chat_participant_jids)]


    return Chat(**chat)


def build_all_chats(
    msgdb_cursor: sqlite3.Cursor, contacts: Dict[str, List[Contact]]
) -> Generator[Chat, None, None]:
    """Extract all chats in the msgdb database.

    It takes a cursor to the message database and a cursor to the wa database, and returns a generator
    that yields a chat object for each chat in the message database.

    Args:
        msgdb_cursor (sqlite3.Cursor): The cursor for the 'msgdb' database.
        contacts (Dict[str, List[Contact]]): Dict of all contacts and jid as key.

    Return:
        A generator of Chat objects.
    """
    query = "SELECT chat._id FROM 'chat'"
    execution = msgdb_cursor.execute(query)
    res_query = list(chain.from_iterable(execution.fetchall()))

    return (
        build_chat_for_given_id_or_phone_number(
            msgdb_cursor=msgdb_cursor, contacts=contacts, chat_row_id=chat_id
        )
        for chat_id in res_query
    )
