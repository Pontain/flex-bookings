from sqlalchemy import String, ForeignKey, DateTime, func, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.mixins import TimestampMixin
from app.core.database import Base


class OrganizationMember(Base, TimestampMixin):
    __tablename__ = "organization_members"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_user_organization"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE")
    )

    role: Mapped[str] = mapped_column(String(30), default="member")


    user: Mapped["User"] = relationship(
        back_populates="organization_memberships"
    )
    organization: Mapped["Organization"] = relationship(
        back_populates="members"
    )