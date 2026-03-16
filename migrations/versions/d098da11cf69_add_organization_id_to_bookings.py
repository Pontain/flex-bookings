"""add organization id to bookings

Revision ID: d098da11cf69
Revises: a7c437f87348
Create Date: 2026-03-16 13:51:24.965306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd098da11cf69'
down_revision: Union[str, Sequence[str], None] = 'a7c437f87348'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("organization_id", sa.Integer(), nullable=True)
    )

    op.create_foreign_key(
        "fk_bookings_organization_id_organizations",
        "bookings",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_bookings_organization_id",
        "bookings",
        ["organization_id"],
        unique=False,
    )

    op.execute("""
        UPDATE bookings
        SET organization_id = venues.organization_id
        FROM venues
        WHERE bookings.venue_id = venues.id
    """)

    op.alter_column("bookings", "organization_id", nullable=False)


def downgrade() -> None:
    op.drop_index("ix_bookings_organization_id", table_name="bookings")
    op.drop_constraint(
        "fk_bookings_organization_id_organizations",
        "bookings",
        type_="foreignkey",
    )
    op.drop_column("bookings", "organization_id")