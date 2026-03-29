"""SQLite engine and session for reservation_service (one DB per service)."""

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

DB_PATH = Path(__file__).resolve().parent / "reservations.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # SQLite: add ends_at_sim if DB existed before this column
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info(reservations)")).fetchall()
        names = {row[1] for row in cols}
        if names and "ends_at_sim" not in names:
            conn.execute(
                text("ALTER TABLE reservations ADD COLUMN ends_at_sim VARCHAR")
            )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reservation_to_dict(r) -> dict:
    return {
        "id": r.id,
        "spot_id": r.spot_id,
        "hours": r.hours,
        "rate": r.rate,
        "total": r.total,
        "created_at": r.created_at,
        "status": r.status,
        "ends_at_sim": r.ends_at_sim,
    }
