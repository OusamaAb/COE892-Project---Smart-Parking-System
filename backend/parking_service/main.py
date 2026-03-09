"""
parking_service — Manages parking spot metadata and status.

This is the source of truth for which spots exist and whether each
spot is free or occupied.  Other services (sensor, reservation) call
this service to update spot status.

Port: 8001
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Parking Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory spot store
# ---------------------------------------------------------------------------
_spots: list[dict] = [
    {"id": 1,  "label": "A1", "status": "free", "reserved": False},
    {"id": 2,  "label": "A2", "status": "free", "reserved": False},
    {"id": 3,  "label": "A3", "status": "occupied", "reserved": True},
    {"id": 4,  "label": "A4", "status": "free", "reserved": False},
    {"id": 5,  "label": "A5", "status": "occupied", "reserved": True},
    {"id": 6,  "label": "B1", "status": "free", "reserved": False},
    {"id": 7,  "label": "B2", "status": "occupied", "reserved": True},
    {"id": 8,  "label": "B3", "status": "free", "reserved": False},
    {"id": 9,  "label": "B4", "status": "free", "reserved": False},
    {"id": 10, "label": "B5", "status": "free", "reserved": False},
    {"id": 11, "label": "C1", "status": "occupied", "reserved": True},
    {"id": 12, "label": "C2", "status": "free", "reserved": False},
    {"id": 13, "label": "C3", "status": "free", "reserved": False},
    {"id": 14, "label": "C4", "status": "occupied", "reserved": True},
    {"id": 15, "label": "C5", "status": "free", "reserved": False},
    {"id": 16, "label": "D1", "status": "free", "reserved": False},
    {"id": 17, "label": "D2", "status": "free", "reserved": False},
    {"id": 18, "label": "D3", "status": "occupied", "reserved": True},
    {"id": 19, "label": "D4", "status": "free", "reserved": False},
    {"id": 20, "label": "D5", "status": "free", "reserved": False},
]


def _find(spot_id: int) -> dict | None:
    return next((s for s in _spots if s["id"] == spot_id), None)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class SpotUpdate(BaseModel):
    status: str | None = None
    reserved: bool | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/spots")
def get_spots():
    return _spots


@app.get("/spots/{spot_id}")
def get_spot(spot_id: int):
    spot = _find(spot_id)
    if not spot:
        raise HTTPException(404, f"Spot {spot_id} not found")
    return spot


@app.patch("/spots/{spot_id}")
def update_spot(spot_id: int, body: SpotUpdate):
    spot = _find(spot_id)
    if not spot:
        raise HTTPException(404, f"Spot {spot_id} not found")
    if body.status is not None:
        spot["status"] = body.status
    if body.reserved is not None:
        spot["reserved"] = body.reserved
    return spot


@app.get("/health")
def health():
    return {"service": "parking", "status": "ok"}
