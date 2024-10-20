from typing import Dict, List

from src.models import Contact

def contacts_to_txt_formatted(contacts: Dict[str, List[Contact]], file_name: str) -> None:
    lines = []

    # Collect lines to write
    for jid, contact_list in contacts.items():
        for contact in contact_list:
            # if contact.number and contact.raw_string_jid.endswith('@s.whatsapp.net'):
            if contact.number:
                if contact.name and contact.number:
                    lines.append(f"{contact.name} ({contact.number}) {contact.raw_string_jid}\n")
                elif contact.number:
                    lines.append(f"{contact.number} {contact.raw_string_jid}\n")
                else:
                    lines.append(f"{contact.raw_string_jid}\n")

    # Sort the collected lines alphabetically
    lines.sort()

    # Write sorted lines to file
    with open(file_name, 'w', encoding="utf-8") as f:
        f.writelines(lines)
