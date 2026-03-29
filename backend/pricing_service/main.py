"""
pricing_service — Computes dynamic parking rates.

Reads lot occupancy from parking_service and applies surge pricing.
Other services call GET /rate to get the current price.  The gateway
enriches spot data with the current rate before returning to the UI.

Port: 8004
"""

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PARKING_URL = "http://localhost:8001"
BASE_RATE = 5.00

app = FastAPI(title="Pricing Service", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


def _surge(ratio: float) -> float:
    """Surge multiplier based on occupancy ratio."""
    if ratio >= 0.9:
        return 2.0
    if ratio >= 0.7:
        return 1.5
    if ratio >= 0.4:
        return 1.25
    return 1.0


@app.get("/rate")
async def get_rate(extra_occupied: int = 0):
    """
    Return hourly rate and occupancy info.

    extra_occupied: pretend this many additional cars are in the lot when
    computing surge (for “next parker” preview). Clamped so effective
    count never exceeds total spaces.
    """
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{PARKING_URL}/spots", timeout=5.0)
    spots = res.json()
    total = len(spots)
    occupied = sum(1 for s in spots if s["status"] == "occupied")
    extra = max(0, int(extra_occupied))
    effective = min(total, occupied + extra)
    ratio = effective / total if total else 0
    multiplier = _surge(ratio)
    rate = round(BASE_RATE * multiplier, 2)
    return {
        "rate": rate,
        "base_rate": BASE_RATE,
        "multiplier": multiplier,
        "occupancy": round(ratio, 3),
        "occupied": occupied,
        "effective_occupied": effective,
        "total": total,
        "extra_occupied": extra,
    }


@app.post("/calculate")
async def calculate(body: dict):
    """Calculate total cost for given hours at the current rate."""
    hours = body.get("hours", 1)
    rate_info = await get_rate()
    total = round(rate_info["rate"] * hours, 2)
    return {"rate": rate_info["rate"], "hours": hours, "total": total}


@app.get("/health")
def health():
    return {"service": "pricing", "status": "ok"}
