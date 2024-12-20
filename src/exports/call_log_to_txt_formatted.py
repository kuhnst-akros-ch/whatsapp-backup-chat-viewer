from datetime import datetime, timezone

from src.common import contact_to_str, contact_to_full_str
from src.models import CallLog, Call


def call_log_to_txt_formatted(call_log: CallLog, folder: str) -> None:
    """Format call logs in a readable format and store them as a text file.

    Args:
        call_log (CallLog): CallLog to be formatted.
        folder (str): Directory to write the formatted call log.

    Returns:
        None: Creates .txt file of the call log in the given directory.
    """
    call_log_list = []

    caller_id_details = contact_to_str(call_log.caller_id)
    caller_id_details_full = contact_to_full_str(call_log.caller_id)

    for call in call_log.calls:
        if call:
            date_time = datetime.fromtimestamp(int(call.timestamp) / 1000, timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            if call.from_me:
                call_log_str = call_from_me_formatted(call, caller_id_details, date_time)
            else:
                call_log_str = call_to_me_formatted(call, caller_id_details, date_time)

            call_log_list.append(call_log_str)

    call_logs = "\n".join(call_log_list)

    file_name = contact_to_str(call_log.caller_id).replace("/", "_") + ".txt"
    with open(f"{folder}/{file_name}", "w", encoding="utf-8") as file:
        file.write(f"{caller_id_details_full}\n\n{call_logs}")


def call_to_me_formatted(call: Call, caller_id_details : str, date_time: str) -> str:
    return (
        f"[{date_time}]: {caller_id_details} ----> Me\n\t>>> Call Type: 📹 - Video Call\n\t>>> Duration: {seconds_to_hms(duration_in_sec=call.duration)}\n\t>>> Status: {call.call_result}"
        if call.video_call
        else f"[{date_time}]: {caller_id_details} ----> Me\n\t>>> Call Type: 📞 - Voice Call\n\t>>> Duration: {seconds_to_hms(duration_in_sec=call.duration)}\n\t>>> Status: {call.call_result}"
    )


def call_from_me_formatted(call: Call, caller_id_details: str, date_time: str) -> str:
    return (
        f"[{date_time}]: Me ----> {caller_id_details}\n\t>>> Call Type: 📹 - Video Call\n\t>>> Duration: {seconds_to_hms(duration_in_sec=call.duration)}\n\t>>> Status: {call.call_result}"
        if call.video_call
        else f"[{date_time}]: Me ----> {caller_id_details}\n\t>>> Call Type: 📞 - Voice Call\n\t>>> Duration: {seconds_to_hms(duration_in_sec=call.duration)}\n\t>>> Status: {call.call_result}"
    )


def seconds_to_hms(duration_in_sec: int) -> str:
    """Convert seconds to hours, minutes and seconds for better representation.

    Args:
        duration_in_sec (int): duration in seconds

    Returns:
        str: Either hours, minutes or seconds based on the converted duration.
    """
    hours = (duration_in_sec // 3600) % 24
    minutes = (duration_in_sec // 60) % 60
    seconds = duration_in_sec % 60

    if hours != 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d} hours"
    elif minutes != 0:
        return f"{minutes:02d}:{seconds:02d} minutes"
    else:
        return f"{seconds:02d} seconds"