#backend/routes.py
#python id="routes1"

from fastapi import APIRouter
from pydantic import BaseModel
from google_maps import get_routes
from ai_engine import decide_reroute

router = APIRouter()

class RouteRequest(BaseModel):
    origin: str
    destination: str

@router.post("/route")
def route(req: RouteRequest):

    routes = get_routes(req.origin, req.destination)

    result = decide_reroute(routes)

    return result

