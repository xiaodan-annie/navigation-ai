from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
import requests

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 1. "TOOLS" LAYER (fake data sources)
# ---------------------------

def get_route_data(origin, destination):

    api_key = os.getenv("ORS_API_KEY")

    # -------------------------
    # Step 1: Geocode origin
    # -------------------------

    geo_url = "https://api.openrouteservice.org/geocode/search"

    origin_res = requests.get(
        geo_url,
        params={
            "api_key": api_key,
            "text": origin
        }
    ).json()

    dest_res = requests.get(
        geo_url,
        params={
            "api_key": api_key,
            "text": destination
        }
    ).json()

    origin_coords = origin_res["features"][0]["geometry"]["coordinates"]
    dest_coords = dest_res["features"][0]["geometry"]["coordinates"]

    # -------------------------
    # Step 2: Route API
    # -------------------------

    route_url = "https://api.openrouteservice.org/v2/directions/driving-car"

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            origin_coords,
            dest_coords
        ]
    }
    route_res = requests.post(
        route_url,
        json=body,
        headers=headers
    ).json()

    route = route_res["routes"][0]
    summary = route["summary"]

    geometry = route["geometry"]
    steps = route["segments"][0]["steps"]
    directions = []
    for step in steps:
        directions.append(step["instruction"])

    distance_meters = summary["distance"]
    duration_seconds = summary["duration"]

    distance_miles = round(distance_meters / 1609.34, 1)
    duration_minutes = round(duration_seconds / 60)
    """
    return {
    "distance_miles": round(summary["distance"] / 1609.34, 1),
    "base_time_min": round(summary["duration"] / 60),
    "origin_coords": origin_coords,
    "destination_coords": dest_coords,
    "geometry": geometry,
    "directions": directions
    }
    """
    return {
    "distance_miles": distance_miles,
    "base_time_min": duration_minutes,
    "origin_coords": origin_coords,
    "destination_coords": dest_coords,
    "geometry": geometry,
    "directions": directions
    }


def get_traffic_context(origin, destination):
    # simple simulation logic
    return {
        "condition": "heavy",
        "rush_hour": True
    }

# ---------------------------
# 2. AI REASONING LAYER
# ---------------------------

def ai_reasoner(route, traffic):
    distance = route["distance_miles"]
    base_time = route["base_time_min"]

    if traffic["condition"] == "heavy":
        eta = base_time + 20
        recommendation = "Leave before 7:30 AM or after 9:30 AM"
    else:
        eta = base_time
        recommendation = "Normal traffic expected"

    return {
        "eta_minutes": eta,
        "traffic": traffic["condition"],
        "recommendation": recommendation
    }

# ---------------------------
# 3. AI LANGUAGE GENERATION LAYER
# ---------------------------

def ai_narrator(origin, destination, route, analysis):
    return (
        f"The route from {origin} to {destination} is about "
        f"{route['distance_miles']} miles. "
        f"Expected travel time is around {analysis['eta_minutes']} minutes. "
        f"Traffic conditions are {analysis['traffic']}. "
        f"Recommendation: {analysis['recommendation']}."
    )

# ---------------------------
# 4. MAIN AGENT ENDPOINT
# ---------------------------
@app.post("/route")
async def route(data: dict):

    origin = data["origin"]
    destination = data["destination"]

    # Step 1: tools
    route_data = get_route_data(origin, destination)
    traffic_data = get_traffic_context(origin, destination)

    # Step 2: reasoning
    analysis = ai_reasoner(route_data, traffic_data)

    # Step 3: local AI explanation
    summary = ai_narrator(
        origin,
        destination,
        route_data,
        analysis
    )

    # Step 4: OpenAI AI generation
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
Traffic level: {analysis['traffic']}

Provide:

1. Travel advice
2. Best departure timing
3. Congestion expectations
4. Alternate suggestions if useful

Keep response under 4 sentences.
"""
                }
            ]
        )

        ai_summary = response.choices[0].message.content
    
    except Exception as e:

        print("OPENAI ERROR:", e)

        ai_summary = (
            f"AI service temporarily unavailable. "
            f"Travel from {origin} to {destination} may experience moderate traffic."
        )
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

