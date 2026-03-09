"""
reservation_service — Manages parking reservations and billing.

Drivers create reservations after parking.  This service calls
pricing_service to compute the cost and parking_service to mark
the spot as reserved (so the sensor won't free it on car_left).

Port: 8003
"""

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime

PARKING_URL = "http://localhost:8001"
PRICING_URL = "http://localhost:8004"

app = FastAPI(title="Reservation Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory reservation store
# ---------------------------------------------------------------------------
_reservations: dict[int, dict] = {}
_next_id = 1


class ReservationRequest(BaseModel):
    spot_id: int
    hours: int = 1


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/reservations")
async def create_reservation(req: ReservationRequest):
    """Create a reservation: compute cost, mark spot as reserved."""
    global _next_id

    # Get current price from pricing_service
    async with httpx.AsyncClient() as client:
        price_res = await client.get(f"{PRICING_URL}/rate", timeout=5.0)
    rate = price_res.json()["rate"]
    total = round(rate * req.hours, 2)

    # Mark spot as reserved in parking_service
    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{PARKING_URL}/spots/{req.spot_id}",
            json={"status": "occupied", "reserved": True},
            timeout=5.0,
        )

    reservation = {
        "id": _next_id,
        "spot_id": req.spot_id,
        "hours": req.hours,
        "rate": rate,
        "total": total,
        "created_at": datetime.utcnow().isoformat(),
        "status": "active",
    }
    _reservations[_next_id] = reservation
    _next_id += 1

    return reservation


@app.get("/reservations")
def list_reservations():
    return list(_reservations.values())


@app.get("/reservations/spot/{spot_id}")
def check_spot_reservation(spot_id: int):
    """Check whether a spot has an active reservation."""
    for r in _reservations.values():
        if r["spot_id"] == spot_id and r["status"] == "active":
            return {"has_reservation": True, "reservation": r}
    return {"has_reservation": False}


@app.delete("/reservations/{res_id}")
async def release_reservation(res_id: int):
    """Release a reservation and free the spot."""
    if res_id not in _reservations:
        raise HTTPException(404, f"Reservation {res_id} not found")

    reservation = _reservations[res_id]
    reservation["status"] = "completed"

    # Free the spot in parking_service
    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{PARKING_URL}/spots/{reservation['spot_id']}",
            json={"status": "free", "reserved": False},
            timeout=5.0,
        )

    return {"released": True, "reservation": reservation}


@app.get("/health")
def health():
    return {"service": "reservation", "status": "ok"}
