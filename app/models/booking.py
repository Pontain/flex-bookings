from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import TimestampMixin
from app.core.database import Base
from app.models.organization import Organization


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    __table_args__ = (
        Index("ix_bookings_venue_time", "venue_id", "start_time", "end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
    )

    venue_id: Mapped[int] = mapped_column(
        ForeignKey("venues.id", ondelete="CASCADE"),
        index=True,
    )

    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)

    contact_name: Mapped[str] = mapped_column(String(120))
    contact_email: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    status: Mapped[str] = mapped_column(String(30), default="confirmed")

    venue: Mapped["Venue"] = relationship(back_populates="bookings")
    organization: Mapped["Organization"] = relationship( back_populates="bookings")