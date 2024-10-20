from typing import Dict, List

from src.models import Contact


def filter_contacts(contacts: Dict[str, List[Contact]]) -> Dict[str, List[Contact]]:
    # Filter out contacts without a number, they are chat-groups
    return {
        jid: [contact for contact in contact_list if contact.number]  # Keep contacts with a number
        for jid, contact_list in contacts.items()
        if any(contact.number for contact in contact_list)  # Ensure we keep only jids that have contacts with numbers
    }

def contacts_to_txt_formatted(contacts: Dict[str, List[Contact]], file: str) -> None:
    with open(file, 'w', encoding="utf-8") as file:
        for jid, contact_list in contacts.items():
            for contact in contact_list:
                if contact.name and contact.number:
                    file.write(f"{contact.name} ({contact.number}) {contact.raw_string_jid}\n")
                elif contact.number:
                    file.write(f"{contact.number} {contact.raw_string_jid}\n")
                else:
                    file.write(f"{contact.raw_string_jid}\n")