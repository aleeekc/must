import requests
import json

data = {
    "participants": ["Randall Cassady", "Marilyn Mckeown"],  # Mandatory
    "meeting_length": "30",  # minutes; Optional
    "earliest": "2/27/2015 2:30:00 PM",  # Optional
    "latest": "2/27/2020 9:30:00 PM",  # Optional
    "office_hours": "9-17"  # Optional
}

r = requests.get("http://127.0.0.1:8000/meeting", data=json.dumps(data))

print(r.content)
