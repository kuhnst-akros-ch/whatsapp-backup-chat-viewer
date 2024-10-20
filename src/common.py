from typing import Dict, List

from src.models import Contact


def contact_resolver(
    contacts: Dict[str, List[Contact]], raw_string_jid: str
) -> Contact:
    """get contact from a dict of all contacts

    Args:
        contacts (Dict[str, List[Contact]]): Dict of all contacts and jid as key.
        raw_string_jid (str): JID of the person who for which contact data is retrieved

    Returns:
        Contact or None
    """
    contact = contacts.get(raw_string_jid)
    if contact:
        # use the last contact
        return contact[-1]
    # return a new contact with just jid
    return Contact(raw_string_jid=raw_string_jid, name=None, number=None)


def contact_to_str(contact: Contact) -> str:
    if contact.name and contact.number:
        return f"{contact.name} ({contact.number})"
    elif contact.number:
        return contact.number
    else:
        return contact.raw_string_jid
