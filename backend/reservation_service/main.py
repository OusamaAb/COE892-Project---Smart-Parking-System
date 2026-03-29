"""
reservation_service — Reservations, billing, and global lot clock.

Lot clock: in-memory only (resets when this process restarts). Starts 9:00 AM;
every REAL_SECONDS_PER_TICK seconds it advances SIM_MINUTES_PER_TICK minutes.
Active reservations store ends_at_sim; when lot time passes that, spots auto-free.

Port: 8003
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SessionLocal, get_db, init_db, reservation_to_dict
from .models import Reservation
from .sim_clock import (
    REAL_SECONDS_PER_TICK,
    SIM_MINUTES_PER_TICK,
    clock_tick_loop,
    format_lot_time,
    get_sim_now,
    reset_sim_clock,
)

PARKING_URL = "http://localhost:8001"
PRICING_URL = "http://localhost:8004"

_tick_task: asyncio.Task | None = None


def _expire_due_reservations_sync() -> None:
    """Free spots whose reservation end time has passed (lot clock)."""
    now = get_sim_now()
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Reservation).where(Reservation.status == "active")
        ).all()
        due: list[Reservation] = []
        for r in rows:
            if not r.ends_at_sim:
                continue
            try:
                end = datetime.fromisoformat(r.ends_at_sim)
            except ValueError:
                continue
            if end <= now:
                due.append(r)
        if not due:
            return
        with httpx.Client(timeout=5.0) as client:
            for r in due:
                r.status = "completed"
                client.patch(
                    f"{PARKING_URL}/spots/{r.spot_id}",
                    json={"status": "free", "reserved": False},
                )
        db.commit()
    finally:
        db.close()


async def _expire_due_reservations_async() -> None:
    await asyncio.to_thread(_expire_due_reservations_sync)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tick_task
    init_db()
    reset_sim_clock()

    async def on_tick() -> None:
        await _expire_due_reservations_async()

    async def runner() -> None:
        await clock_tick_loop(on_tick)

    _tick_task = asyncio.create_task(runner())
    yield
    if _tick_task:
        _tick_task.cancel()
        try:
            await _tick_task
        except asyncio.CancelledError:
            pass
        _tick_task = None


app = FastAPI(title="Reservation Service", version="2.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class ReservationRequest(BaseModel):
    spot_id: int
    hours: int = 1


@app.get("/lot-clock")
def lot_clock():
    """Current simulated lot time (global for all users this session)."""
    now = get_sim_now()
    return {
        "iso": now.isoformat(timespec="seconds"),
        "display": format_lot_time(now),
        "real_seconds_per_tick": REAL_SECONDS_PER_TICK,
        "sim_minutes_per_tick": SIM_MINUTES_PER_TICK,
    }


@app.post("/reservations")
async def create_reservation(req: ReservationRequest, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        price_res = await client.get(f"{PRICING_URL}/rate", timeout=5.0)
    rate = price_res.json()["rate"]
    total = round(rate * req.hours, 2)

    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{PARKING_URL}/spots/{req.spot_id}",
            json={"status": "occupied", "reserved": True},
            timeout=5.0,
        )

    start_sim = get_sim_now()
    ends_sim = start_sim + timedelta(hours=req.hours)

    row = Reservation(
        spot_id=req.spot_id,
        hours=req.hours,
        rate=rate,
        total=total,
        created_at=datetime.utcnow().isoformat(),
        status="active",
        ends_at_sim=ends_sim.isoformat(timespec="seconds"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    out = reservation_to_dict(row)
    out["starts_at_sim_display"] = format_lot_time(start_sim)
    out["ends_at_sim_display"] = format_lot_time(ends_sim)
    return out


@app.get("/reservations")
def list_reservations(db: Session = Depends(get_db)):
    rows = db.scalars(select(Reservation).order_by(Reservation.id)).all()
    return [_reservation_json(r) for r in rows]


def _reservation_json(r: Reservation) -> dict:
    d = reservation_to_dict(r)
    if r.ends_at_sim:
        try:
            end = datetime.fromisoformat(r.ends_at_sim)
            d["ends_at_sim_display"] = format_lot_time(end)
        except ValueError:
            d["ends_at_sim_display"] = None
    else:
        d["ends_at_sim_display"] = None
    return d


@app.get("/reservations/spot/{spot_id}")
def check_spot_reservation(spot_id: int, db: Session = Depends(get_db)):
    row = db.scalars(
        select(Reservation).where(
            Reservation.spot_id == spot_id,
            Reservation.status == "active",
        )
    ).first()
    if row:
        return {"has_reservation": True, "reservation": _reservation_json(row)}
    return {"has_reservation": False}


@app.delete("/reservations/{res_id}")
async def release_reservation(res_id: int, db: Session = Depends(get_db)):
    row = db.get(Reservation, res_id)
    if not row:
        raise HTTPException(404, f"Reservation {res_id} not found")

    row.status = "completed"
    db.commit()
    db.refresh(row)

    async with httpx.AsyncClient() as client:
        await client.patch(
            f"{PARKING_URL}/spots/{row.spot_id}",
            json={"status": "free", "reserved": False},
            timeout=5.0,
        )

    return {"released": True, "reservation": _reservation_json(row)}


@app.get("/health")
def health():
    return {"service": "reservation", "status": "ok"}
