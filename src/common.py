from typing import Dict

from src.models import Contact


def contact_resolver(
    contacts: Dict[str, Contact], raw_string_jid: str
) -> Contact:
    """get contact from a dict of all contacts

    Args:
        contacts (Dict[str, Contact]): Dict of all contacts and jid as key.
        raw_string_jid (str): JID of the person who for which contact data is retrieved

    Returns:
        Contact or None
    """
    contact = contacts.get(raw_string_jid)
    if contact:
        return contact
    return Contact(raw_string_jid=raw_string_jid, name=None, number=None)
