#backend/google_maps.py
#python id="gm1"
import requests

API_KEY = "YOUR_GOOGLE_API_KEY"

def get_routes(origin, destination):

    url = "https://maps.googleapis.com/maps/api/directions/json"

    params = {
        "origin": origin,
        "destination": destination,
        "alternatives": "true",
        "departure_time": "now",
        "key": API_KEY
    }

    res = requests.get(url, params=params)
    data = res.json()

    return data["routes"]
