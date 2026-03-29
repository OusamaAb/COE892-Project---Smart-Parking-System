"""
parking_service — Manages parking spot metadata and status.

Persists to SQLite (parking.db in this package). Other services call
this API to read/update spot state.

Port: 8001
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import get_db, init_db, spot_to_dict
from .models import Spot


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Parking Service", version="2.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class SpotUpdate(BaseModel):
    status: str | None = None
    reserved: bool | None = None


@app.get("/spots")
def get_spots(db: Session = Depends(get_db)):
    rows = db.scalars(select(Spot).order_by(Spot.id)).all()
    return [spot_to_dict(s) for s in rows]


@app.get("/spots/{spot_id}")
def get_spot(spot_id: int, db: Session = Depends(get_db)):
    spot = db.get(Spot, spot_id)
    if not spot:
        raise HTTPException(404, f"Spot {spot_id} not found")
    return spot_to_dict(spot)


@app.patch("/spots/{spot_id}")
def update_spot(spot_id: int, body: SpotUpdate, db: Session = Depends(get_db)):
    spot = db.get(Spot, spot_id)
    if not spot:
        raise HTTPException(404, f"Spot {spot_id} not found")
    if body.status is not None:
        spot.status = body.status
    if body.reserved is not None:
        spot.reserved = body.reserved
    db.commit()
    db.refresh(spot)
    return spot_to_dict(spot)


@app.get("/health")
def health():
    return {"service": "parking", "status": "ok"}
