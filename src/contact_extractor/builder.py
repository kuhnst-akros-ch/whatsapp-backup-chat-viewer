from typing import Dict

from ..models import Contact


# Function to fetch contacts and return a dictionary with jid as key and Contact as value
def build_all_contacts(wadb_cursor) -> Dict[str, Contact]:
    # Define the query
    query = "SELECT jid, number, display_name FROM wa_contacts"

    # Execute the query using the existing cursor
    execution = wadb_cursor.execute(query)

    # Fetch all rows
    rows = execution.fetchall()

    # Create a dictionary mapping the result to the column names
    return {
        row["jid"]: Contact(
            raw_string_jid=row["jid"],  # jid mapped to raw_string_jid
            name=row["display_name"],   # display_name mapped to name
            number=row["number"]        # number mapped to number
        )
        for row in [dict(zip([col[0] for col in execution.description], row)) for row in rows]
    }
