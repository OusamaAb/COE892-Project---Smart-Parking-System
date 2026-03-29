"""SQLAlchemy models for reservation_service."""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    spot_id: Mapped[int] = mapped_column(index=True)
    hours: Mapped[int]
    rate: Mapped[float]
    total: Mapped[float]
    created_at: Mapped[str]
    status: Mapped[str] = mapped_column(default="active")
    # Lot simulation: ISO naive datetime when reservation ends (lot clock)
    ends_at_sim: Mapped[str | None] = mapped_column(default=None)
