"""SQLite engine and session for parking_service (one DB per service)."""

from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Spot

DB_PATH = Path(__file__).resolve().parent / "parking.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initial lot layout (seeded only when DB is empty)
INITIAL_SPOTS: list[dict] = [
    {"id": 1, "label": "A1", "status": "free", "reserved": False},
    {"id": 2, "label": "A2", "status": "free", "reserved": False},
    {"id": 3, "label": "A3", "status": "occupied", "reserved": True},
    {"id": 4, "label": "A4", "status": "free", "reserved": False},
    {"id": 5, "label": "A5", "status": "occupied", "reserved": True},
    {"id": 6, "label": "B1", "status": "free", "reserved": False},
    {"id": 7, "label": "B2", "status": "occupied", "reserved": True},
    {"id": 8, "label": "B3", "status": "free", "reserved": False},
    {"id": 9, "label": "B4", "status": "free", "reserved": False},
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


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        n = db.scalar(select(func.count()).select_from(Spot))
        if n == 0:
            for row in INITIAL_SPOTS:
                db.add(Spot(**row))
            db.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def spot_to_dict(s: Spot) -> dict:
    return {
        "id": s.id,
        "label": s.label,
        "status": s.status,
        "reserved": s.reserved,
    }
