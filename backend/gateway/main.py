"""
gateway — API Gateway / Backend-for-Frontend (BFF).

The React frontend talks only to this service.  The gateway fans out
requests to the internal microservices and aggregates responses.
This is the only service that exposes CORS for the browser.

Port: 8000
"""

import os

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PARKING_URL     = "http://localhost:8001"
SENSOR_URL      = "http://localhost:8002"
RESERVATION_URL = "http://localhost:8003"
PRICING_URL     = "http://localhost:8004"

app = FastAPI(title="Smart Parking Gateway", version="2.0.0")

_cors_extra = os.getenv("GATEWAY_CORS_ORIGINS", "")
_allow_origins = ["http://localhost:5173"]
_allow_origins.extend(
    o.strip() for o in _cors_extra.split(",") if o.strip()
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health — checks each downstream service
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    statuses = {}
    for name, url in [
        ("parking", PARKING_URL),
        ("sensor", SENSOR_URL),
        ("reservation", RESERVATION_URL),
        ("pricing", PRICING_URL),
    ]:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(f"{url}/health", timeout=2.0)
                statuses[name] = r.json().get("status", "ok")
        except Exception:
            statuses[name] = "unavailable"
    return {"gateway": "ok", "services": statuses}


# ---------------------------------------------------------------------------
# Spots — enriches parking data with current price from pricing_service
# ---------------------------------------------------------------------------
@app.get("/spots")
async def get_spots(
    extra_occupied: int = Query(
        1,
        ge=0,
        le=100,
        description="Extra cars assumed for surge preview (0=actual only, 1=next parker)",
    ),
):
    """Aggregate spots + pricing into a single response for the UI."""
    async with httpx.AsyncClient() as client:
        spots_res = await client.get(f"{PARKING_URL}/spots", timeout=5.0)
        price_res = await client.get(
            f"{PRICING_URL}/rate",
            params={"extra_occupied": extra_occupied},
            timeout=5.0,
        )
    spots = spots_res.json()
    rate_info = price_res.json()
    rate = rate_info["rate"]

    for spot in spots:
        spot["price"] = rate

    return spots


# ---------------------------------------------------------------------------
# Sensor events — proxy to sensor_service
# ---------------------------------------------------------------------------
class SensorEventReq(BaseModel):
    spot_id: int
    event_type: str


@app.post("/sensor-event")
async def sensor_event(body: SensorEventReq):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{SENSOR_URL}/events",
            json=body.model_dump(),
            timeout=5.0,
        )
    return res.json()


# ---------------------------------------------------------------------------
# Reservations — proxy to reservation_service
# ---------------------------------------------------------------------------
class ReservationReq(BaseModel):
    spot_id: int
    hours: int = 1


@app.post("/reservations")
async def create_reservation(body: ReservationReq):
    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{RESERVATION_URL}/reservations",
            json=body.model_dump(),
            timeout=5.0,
        )
    return res.json()


@app.get("/reservations")
async def list_reservations():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{RESERVATION_URL}/reservations", timeout=5.0)
    return res.json()


@app.get("/reservations/spot/{spot_id}")
async def check_spot_reservation(spot_id: int):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{RESERVATION_URL}/reservations/spot/{spot_id}",
            timeout=5.0,
        )
    return res.json()


@app.delete("/reservations/{res_id}")
async def release_reservation(res_id: int):
    async with httpx.AsyncClient() as client:
        res = await client.delete(
            f"{RESERVATION_URL}/reservations/{res_id}",
            timeout=5.0,
        )
    if res.status_code >= 400:
        raise HTTPException(res.status_code, res.json().get("detail", "Error"))
    return res.json()


# ---------------------------------------------------------------------------
# Pricing — proxy current rate
# ---------------------------------------------------------------------------
@app.get("/pricing/rate")
async def get_rate(
    extra_occupied: int = Query(0, ge=0, le=100),
):
    async with httpx.AsyncClient() as client:
        res = await client.get(
            f"{PRICING_URL}/rate",
            params={"extra_occupied": extra_occupied},
            timeout=5.0,
        )
    return res.json()


# ---------------------------------------------------------------------------
# Lot clock (simulated time — session only, reservation service)
# ---------------------------------------------------------------------------
@app.get("/lot-clock")
async def lot_clock():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{RESERVATION_URL}/lot-clock", timeout=5.0)
    return res.json()
