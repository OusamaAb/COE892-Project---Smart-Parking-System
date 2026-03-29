"""SQLAlchemy models for parking_service."""

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Spot(Base):
    __tablename__ = "spots"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="free")
    reserved: Mapped[bool] = mapped_column(default=False)
