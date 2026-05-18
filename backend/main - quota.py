from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os

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
    # later: replace with Google Maps / OpenRouteService
    return {
        "distance_miles": 38,
        "base_time_min": 45
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
Analyze travel from {origin} to {destination}.

Give short traffic/travel advice in 2 sentences.
"""
            }
        ]
    )

    ai_summary = response.choices[0].message.content

    return {
        "origin": origin,
        "destination": destination,
        "distance": f"{route_data['distance_miles']} miles",
        "eta": f"{analysis['eta_minutes']} min",
        "traffic": analysis["traffic"],
        "recommendation": analysis["recommendation"],
        "summary": summary,
        "ai_summary": ai_summary,
        "status": "success"
    }
