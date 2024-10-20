from collections import defaultdict
from typing import Dict, List

from ..models import Contact


# Function to fetch contacts and return a dictionary with jid as key and Contact as value
def build_all_contacts(wadb_cursor) -> Dict[str, List[Contact]]:
    # Define the query
    query = "SELECT jid, number, display_name FROM wa_contacts"

    # Execute the query using the existing cursor
    execution = wadb_cursor.execute(query)

    # Fetch all rows
    rows = execution.fetchall()

    # Create a defaultdict to handle multiple contacts per jid
    contacts_dict = defaultdict(list)

    # Populate the dictionary, adding contacts to a list for each jid
    for row in [dict(zip([col[0] for col in execution.description], row)) for row in rows]:
        contacts_dict[row["jid"]].append(
            Contact(
                raw_string_jid=row["jid"],  # jid mapped to raw_string_jid
                name=row["display_name"],   # display_name mapped to name
                number=row["number"]        # number mapped to number
            )
        )

    return dict(contacts_dict)  # Convert back to a regular dictionary
