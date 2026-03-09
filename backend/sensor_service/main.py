"""
sensor_service — Simulates IoT sensors that detect car presence.

When the frontend's drivable car overlaps a parking bay, it sends an
event here.  This service then calls parking_service to update the
spot status, and checks reservation_service before freeing a spot.

Port: 8002
"""

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

PARKING_URL = "http://localhost:8001"
RESERVATION_URL = "http://localhost:8003"

app = FastAPI(title="Sensor Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory sensor state — tracks which spots currently have a car detected
# ---------------------------------------------------------------------------
_active_sensors: dict[int, dict] = {}   # spot_id → {detected_at, ...}


class SensorEvent(BaseModel):
    spot_id: int
    event_type: str   # "car_entered" or "car_left"


@app.post("/events")
async def receive_event(event: SensorEvent):
    """
    Process a sensor event from the IoT layer (or the frontend simulation).

    car_entered → mark spot occupied via parking_service
    car_left    → if no active reservation, mark spot free
    """
    if event.event_type == "car_entered":
        _active_sensors[event.spot_id] = {
            "detected_at": datetime.utcnow().isoformat(),
        }
        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{PARKING_URL}/spots/{event.spot_id}",
                json={"status": "occupied"},
                timeout=5.0,
            )
        return {"action": "spot_occupied", "spot_id": event.spot_id}

    elif event.event_type == "car_left":
        _active_sensors.pop(event.spot_id, None)

        # Check if the spot has an active reservation before freeing
        has_reservation = False
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{RESERVATION_URL}/reservations/spot/{event.spot_id}",
                    timeout=5.0,
                )
                has_reservation = res.json().get("has_reservation", False)
        except Exception:
            has_reservation = False

        if not has_reservation:
            async with httpx.AsyncClient() as client:
                await client.patch(
                    f"{PARKING_URL}/spots/{event.spot_id}",
                    json={"status": "free", "reserved": False},
                    timeout=5.0,
                )
            return {"action": "spot_freed", "spot_id": event.spot_id}

        return {"action": "spot_reserved_kept", "spot_id": event.spot_id}

    raise HTTPException(400, f"Unknown event_type: {event.event_type}")


@app.get("/status")
def sensor_status():
    """Return which spots currently have a car physically present."""
    return _active_sensors


@app.get("/health")
def health():
    return {"service": "sensor", "status": "ok"}
