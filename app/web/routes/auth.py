from datetime import datetime, timedelta
import os
import secrets
import token

from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.email import send_password_reset_email

from app.api.deps import get_db
from app.core import email
from app.core.security import verify_password, hash_password
from app.models import user
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


@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_form(request: Request):
    return templates.TemplateResponse(
        "auth/forgot_password.html",
        {"request": request}
    )


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

    # Viktigt: visa samma meddelande även om mailen inte finns
    if user:
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expires_at = datetime.now() + timedelta(hours=1)

        db.add(user)
        db.commit()

    app_base_url = os.getenv("APP_BASE_URL", "http://127.0.0.1:8010")
    reset_link = f"{app_base_url}/reset-password/{token}"

    print("RESET LINK:", reset_link)

    await send_password_reset_email(
    to_email=user.email,
    reset_link=reset_link,
)

    return templates.TemplateResponse(
        "auth/forgot_password_sent.html",
        {"request": request}
    )


@router.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_form(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.reset_token == token).first()

    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.now():
        return templates.TemplateResponse(
            "auth/reset_password_invalid.html",
            {"request": request}
        )

    return templates.TemplateResponse(
        "auth/reset_password.html",
        {
            "request": request,
            "token": token,
        }
    )


@router.post("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_submit(
    token: str,
    request: Request,
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.reset_token == token).first()

    if not user or not user.reset_token_expires_at or user.reset_token_expires_at < datetime.now():
        return templates.TemplateResponse(
            "auth/reset_password_invalid.html",
            {"request": request}
        )

    user.hashed_password = hash_password(password)
    user.reset_token = None
    user.reset_token_expires_at = None

    db.add(user)
    db.commit()

    return RedirectResponse(
        url="/login?password_reset=1",
        status_code=303
    )