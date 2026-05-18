##backend/ai_engine.py (🔥 SIMPLE RULE ENGINE)
#This is your “AI”.
#python id="ai1"

def decide_reroute(routes):

    analyzed = []

    for r in routes:

        leg = r["legs"][0]

        duration = leg["duration"]["value"]

        traffic = leg.get("duration_in_traffic", leg["duration"])["value"]

        analyzed.append({
            "summary": r.get("summary", ""),
            "duration": duration,
            "traffic_duration": traffic
        })

    best = min(analyzed, key=lambda x: x["traffic_duration"])
    current = analyzed[0]

    savings = current["traffic_duration"] - best["traffic_duration"]

    reroute = savings > 300  # 5 minutes rule

    return {
        "routes": analyzed,
        "best_route": best,
        "reroute": reroute,
        "savings_seconds": savings,
        "message": (
            "Reroute recommended" if reroute else "Current route is fine"
        )
    }

