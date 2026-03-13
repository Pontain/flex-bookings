from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationRead

router = APIRouter()


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_organization(
    organization_data: OrganizationCreate,
    db: Session = Depends(get_db),
):
    existing_organization = db.execute(
        select(Organization).where(Organization.name == organization_data.name)
    ).scalar_one_or_none()

    if existing_organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization with that name already exists.",
        )

    organization = Organization(name=organization_data.name)

    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


@router.get("/", response_model=list[OrganizationRead])
def get_organizations(db: Session = Depends(get_db)):
    organizations = db.execute(
        select(Organization).order_by(Organization.id)
    ).scalars().all()
    return organizations