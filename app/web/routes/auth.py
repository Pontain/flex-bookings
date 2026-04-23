from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import verify_password, hash_password
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.core.templates import templates

router = APIRouter()


@router.get("/")
def root():
    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    created = request.query_params.get("created")

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "created": created,
        }
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    email = email.strip().lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Fel e-post eller lösenord.",
            },
            status_code=400,
        )

    request.session["user_id"] = user.id

    return RedirectResponse(
        url="/dashboard",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request}
    )


@router.post("/register")
def register(
    request: Request,
    organization_name: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    organization_name = organization_name.strip()
    full_name = full_name.strip()
    email = email.strip().lower()

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Det finns redan ett konto med den e-postadressen.",
                "organization_name": organization_name,
                "full_name": full_name,
                "email": email,
            },
            status_code=400,
        )

    existing_organization = db.query(Organization).filter(
        Organization.name == organization_name
    ).first()
    if existing_organization:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Det finns redan en organisation med det namnet.",
                "organization_name": organization_name,
                "full_name": full_name,
                "email": email,
            },
            status_code=400,
        )

    organization = Organization(name=organization_name)
    db.add(organization)
    db.flush()

    user = User(
        organization_id=organization.id,
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()

    membership = OrganizationMember(
        user_id=user.id,
        organization_id=organization.id,
        role="owner",
    )
    db.add(membership)

    db.commit()

    return RedirectResponse(
        url="/login?created=1",
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        url="/login",
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    return templates.TemplateResponse(
        "pages/faq.html",
        {"request": request}
    )