from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel, Field
import os
import requests

app = FastAPI()

# ---------------------------
# CORS (Netlify frontend safe)
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Request Schema
# ---------------------------
class RouteRequest(BaseModel):
    origin: str = Field(min_length=2, max_length=100)
    destination: str = Field(min_length=2, max_length=100)

# ---------------------------
# Environment validation
# ---------------------------
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
ORS_KEY = os.getenv("ORS_API_KEY")

if not OPENAI_KEY:
    raise Exception("Missing OPENAI_API_KEY")

if not ORS_KEY:
    raise Exception("Missing ORS_API_KEY")

client = OpenAI(api_key=OPENAI_KEY)


# ---------------------------
# ORS TOOL LAYER
# ---------------------------
def get_route_data(origin, destination):

    geo_url = "https://api.openrouteservice.org/geocode/search"

    # Geocode origin
    origin_res = requests.get(
        geo_url,
        params={"api_key": ORS_KEY, "text": origin}
    ).json()

    # Geocode destination
    dest_res = requests.get(
        geo_url,
        params={"api_key": ORS_KEY, "text": destination}
    ).json()

    if not origin_res.get("features") or not dest_res.get("features"):
        raise Exception("Geocoding failed")

    origin_coords = origin_res["features"][0]["geometry"]["coordinates"]
    dest_coords = dest_res["features"][0]["geometry"]["coordinates"]

    # Route API
    route_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    route_res = requests.post(
        route_url,
        json={"coordinates": [origin_coords, dest_coords]},
        headers={
            "Authorization": ORS_KEY,
            "Content-Type": "application/json"
        }
    ).json()

    if "routes" not in route_res:
        raise Exception("Routing API failed")

    route = route_res["routes"][0]
    summary = route["summary"]

    distance_miles = round(summary["distance"] / 1609.34, 1)
    duration_minutes = round(summary["duration"] / 60)

    steps = route["segments"][0]["steps"]
    directions = [step["instruction"] for step in steps]

    return {
        "distance_miles": distance_miles,
        "base_time_min": duration_minutes,
        "origin_coords": origin_coords,
        "destination_coords": dest_coords,
        "geometry": route["geometry"],
        "directions": directions
    }


# ---------------------------
# SIMPLE TRAFFIC MODEL
# ---------------------------
def get_traffic_context():
    return {
        "condition": "heavy",
        "rush_hour": True
    }


# ---------------------------
# REASONING LAYER
# ---------------------------
def ai_reasoner(route, traffic):

    base_time = route["base_time_min"]

    if traffic["condition"] == "heavy":
        eta = base_time + 20
        recommendation = "Leave early morning (before 7:30 AM) or after 9:30 AM"
    else:
        eta = base_time
        recommendation = "Normal traffic expected"

    return {
        "eta_minutes": eta,
        "traffic": traffic["condition"],
        "recommendation": recommendation
    }


# ---------------------------
# NATURAL LANGUAGE SUMMARY
# ---------------------------
def ai_narrator(origin, destination, route, analysis):

    return (
        f"The route from {origin} to {destination} is {route['distance_miles']} miles. "
        f"Expected travel time is about {analysis['eta_minutes']} minutes. "
        f"Traffic is {analysis['traffic']}. "
        f"Recommendation: {analysis['recommendation']}."
    )


# ---------------------------
# MAIN ENDPOINT
# ---------------------------
@app.post("/route")
def route(data: RouteRequest):

    origin = data.origin.strip().title()
    destination = data.destination.strip().title()

    try:
        # 1. ORS data
        route_data = get_route_data(origin, destination)

        # 2. Traffic simulation
        traffic_data = get_traffic_context()

        # 3. Reasoning
        analysis = ai_reasoner(route_data, traffic_data)

        # 4. AI summary (OpenAI)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a smart route assistant."
                    },
                    {
                        "role": "user",
                        "content": f"""
Route analysis:

Origin: {origin}
Destination: {destination}
Distance: {route_data['distance_miles']} miles
Estimated time: {analysis['eta_minutes']} minutes
Traffic: {analysis['traffic']}

Give:
- Travel advice
- Best departure time
- Congestion expectation
- Alternative suggestions

Keep under 4 sentences.
"""
                    }
                ]
            )

            ai_summary = response.choices[0].message.content

        except Exception as e:
            print("OPENAI ERROR:", e)
            ai_summary = (
                f"AI unavailable. Expect {analysis['traffic']} traffic "
                f"from {origin} to {destination}."
            )

        # 5. Final response
        return {
            "origin": origin,
            "destination": destination,
            "distance": f"{route_data['distance_miles']} miles",
            "eta": f"{analysis['eta_minutes']} min",
            "traffic": analysis["traffic"],
            "recommendation": analysis["recommendation"],
            "ai_summary": ai_summary,

            "origin_coords": route_data["origin_coords"],
            "destination_coords": route_data["destination_coords"],
            "geometry": route_data["geometry"],
            "directions": route_data["directions"],

            "status": "success"
        }

    except Exception as e:
        print("ROUTE ERROR:", e)

        return {
            "origin": origin,
            "destination": destination,
            "distance": "N/A",
            "eta": "N/A",
            "traffic": "unknown",
            "recommendation": "Unable to calculate route",
            "ai_summary": "Route service temporarily unavailable.",
            "origin_coords": [0, 0],
            "destination_coords": [0, 0],
            "geometry": None,
            "directions": [],
            "status": "error"
        }