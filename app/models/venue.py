from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, func, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import TimestampMixin
from app.core.database import Base


class Venue(Base, TimestampMixin):
    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True
    )

    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


    organization: Mapped["Organization"] = relationship(
        back_populates="venues"
    )

    bookings: Mapped[list["Booking"]] = relationship(
        back_populates="venue",
        cascade="all, delete-orphan"
    )