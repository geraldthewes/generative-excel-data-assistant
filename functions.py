from datetime import datetime
import requests
import json
import pytz

todo_list = []

def add_todo_item(item: str):
    todo_list.append(item)
    return f"Added to-do: {item}"

def list_todo_items() -> str:
    if len(todo_list) == 0:
        return "No to-do items"
    return "\n ".join(todo_list)

def get_next_departure_time(from_station: str, to_station: str) -> str:
    tz = pytz.timezone("Europe/Zurich")
    res = requests.get(
        "http://transport.opendata.ch/v1/connections",
        params={
            "from": from_station,
            "to": to_station,
            "time": datetime.now(tz).strftime("%H:%M"),
        },
    )
    parsed_res = json.loads(res.text)
    if len(parsed_res) == 0:
        return "error, no result came back from the Opendata API"
    datetime_object = datetime.fromtimestamp(
        parsed_res["connections"][0]["from"]["departureTimestamp"], tz
    )
    return datetime_object.strftime("%H:%M:%S")

def caesar_cipher(text: str, shift: str = "3") -> str:
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            result += chr((ord(char) - ascii_offset + int(shift)) % 26 + ascii_offset)
        else:
            result += char
    return result

