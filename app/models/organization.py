from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String

from app.models.mixins import TimestampMixin
from app.core.database import Base


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    members: Mapped[list["OrganizationMember"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    venues: Mapped[list["Venue"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    bookings: Mapped[list["Booking"]] = relationship(
        cascade="all, delete-orphan"
    )

    users: Mapped[list["User"]] = relationship(back_populates="organization")