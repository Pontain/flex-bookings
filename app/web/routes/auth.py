from datetime import datetime, timedelta, timezone
import logging, secrets
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.config import BASE_URL
from app.core.email import send_account_email
from app.core.security import verify_password, hash_password, normalize_email, digest
from app.core.templates import templates
from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
router = APIRouter()
logger = logging.getLogger(__name__)
def now(): return datetime.now(timezone.utc).replace(tzinfo=None)
def page(request, template, **context): return templates.TemplateResponse(request=request, name=template, context=context)
def notice(request, text): return page(request, "auth/notice.html", message=text)
async def issue_verification(db, user):
    token = secrets.token_urlsafe(32)
    user.verification_token = digest(token)
    user.verification_expires_at = now() + timedelta(hours=1)
    db.commit()
    try: await send_account_email(user.email, f"{BASE_URL}/verify-email/{token}", "Verifiera din e-postadress")
    except Exception: logger.error("Verifieringsmeddelandet kunde inte skickas; kontrollera SMTP.")
@router.get("/")
def root(): return RedirectResponse("/login", status_code=303)
@router.get("/login")
def login_page(request: Request): return page(request, "auth/login.html", created=request.query_params.get("created"))
@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == normalize_email(email)).first()
    if not user or not user.is_active or not verify_password(password, user.hashed_password):
        return page(request, "auth/login.html", error="Fel e-post eller lösenord.")
    if not user.email_verified:
        return notice(request, "Verifiera din e-post innan du loggar in. Du kan begära en ny verifieringslänk nedan.")
    request.session.clear()
    request.session.update(user_id=user.id, version=user.session_version, csrf=secrets.token_urlsafe(32))
    return RedirectResponse("/dashboard", status_code=303)
@router.get("/register")
def register_page(request: Request): return page(request, "auth/register.html")
@router.post("/register")
async def register(request: Request, organization_name: str = Form(...), full_name: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    organization_name, full_name = organization_name.strip(), full_name.strip()
    email = normalize_email(email)
    if not 1 <= len(organization_name) <= 120 or not 1 <= len(full_name) <= 120:
        raise HTTPException(400, "Organisation och namn måste innehålla 1–120 tecken.")
    hashed = hash_password(password)
    if db.query(User).filter(User.email == email).first() or db.query(Organization).filter(Organization.name == organization_name).first():
        return page(request, "auth/register.html", error="E-postadressen eller organisationsnamnet är redan registrerat.")
    organization = Organization(name=organization_name)
    db.add(organization); db.flush()
    user = User(organization_id=organization.id, full_name=full_name, email=email, hashed_password=hashed, is_active=True, is_superuser=True, email_verified=False)
    db.add(user); db.flush()
    db.add(OrganizationMember(user_id=user.id, organization_id=organization.id, role="owner"))
    await issue_verification(db, user)
    return notice(request, "Kontot har skapats. Kontrollera din e-post för verifieringslänken. Om den inte kommer kan du begära en ny länk nedan.")
@router.get("/verify-email/{token}")
def verification_page(token: str, request: Request):
    return page(request, "auth/verify.html", token=token)
@router.post("/verify-email/{token}")
def verify_email(token: str, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == digest(token)).with_for_update().first()
    if not user or not user.verification_expires_at or user.verification_expires_at <= now():
        raise HTTPException(400, "Länken är ogiltig eller har gått ut. Begär en ny verifieringslänk.")
    user.email_verified = True; user.verification_token = None; user.verification_expires_at = None
    db.commit()
    return notice(request, "E-postadressen är verifierad. Du kan nu logga in.")
@router.get("/resend-verification")
def resend_page(request: Request): return notice(request, "Begär en ny verifieringslänk.")
@router.post("/resend-verification")
async def resend(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == normalize_email(email)).first()
    if user and user.is_active and not user.email_verified: await issue_verification(db, user)
    return notice(request, "Om adressen tillhör ett konto som behöver verifieras skickas en ny länk.")
@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user = db.get(User, request.session.get("user_id")) if request.session.get("user_id") else None
    if user and request.session.get("version") == user.session_version:
        user.session_version += 1
        db.commit()
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
@router.get("/faq")
def faq_page(request: Request): return page(request, "pages/faq.html")
@router.get("/forgot-password")
def forgot_form(request: Request): return page(request, "auth/forgot_password.html")
@router.post("/forgot-password")
async def forgot_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == normalize_email(email)).first()
    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        user.reset_token = digest(token); user.reset_token_expires_at = now() + timedelta(hours=1)
        db.commit()
        try: await send_account_email(user.email, f"{BASE_URL}/reset-password/{token}", "Återställ lösenord")
        except Exception: logger.error("Återställningsmeddelandet kunde inte skickas; kontrollera SMTP.")
    return page(request, "auth/forgot_password_sent.html")
def reset_user(db, token):
    user = db.query(User).filter(User.reset_token == digest(token)).with_for_update().first()
    if not user or not user.is_active or not user.reset_token_expires_at or user.reset_token_expires_at <= now(): return None
    return user
@router.get("/reset-password/{token}")
def reset_form(token: str, request: Request, db: Session = Depends(get_db)):
    if not reset_user(db, token): return page(request, "auth/reset_password_invalid.html")
    return page(request, "auth/reset_password.html", token=token)
@router.post("/reset-password/{token}")
def reset_password(token: str, request: Request, password: str = Form(...), db: Session = Depends(get_db)):
    user = reset_user(db, token)
    if not user: raise HTTPException(400, "Länken är ogiltig eller har gått ut.")
    user.hashed_password = hash_password(password)
    user.reset_token = None; user.reset_token_expires_at = None; user.session_version += 1
    db.commit(); request.session.clear()
    return RedirectResponse("/login?password_reset=1", status_code=303)
