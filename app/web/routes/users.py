from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.templates import templates
from app.core.dependencies import get_current_user
from app.core.security import hash_password, normalize_email
from app.web.routes.auth import issue_verification
from app.models.user import User
from app.models.organization_member import OrganizationMember

router = APIRouter()


@router.get("/users", response_class=HTMLResponse)
def users_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    users = (
        db.query(User)
        .filter(User.organization_id == current_user.organization_id)
        .order_by(User.id.asc())
        .all()
    )

    return templates.TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "current_user": current_user,
            "users": users,
        }
    )


@router.get("/users/new", response_class=HTMLResponse)
def new_user_form(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    return templates.TemplateResponse(
        "users/new.html",
        {
            "request": request,
            "current_user": current_user,
        }
    )


@router.post("/users/new")
async def create_user(
    full_name: str = Form(""),
    email: str = Form(...),
    password: str = Form(...),
    is_superuser: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    email = normalize_email(email)
    if not 1 <= len(full_name.strip()) <= 120: raise HTTPException(400, "Namn måste innehålla 1–120 tecken")
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    user = User(
        full_name=full_name.strip(),
        email=email,
        hashed_password=hash_password(password),
        is_superuser=True if is_superuser else False,
        is_active=True,
        organization_id=current_user.organization_id,
    )

    db.add(user)
    db.flush()

    membership = OrganizationMember(
        user_id=user.id,
        organization_id=current_user.organization_id,
        role="admin" if user.is_superuser else "member",
    )
    db.add(membership)

    db.commit()
    if not user.email_verified:
        await issue_verification(db, user)

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/users/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Kan inte ta bort dig själv")

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Användaren finns inte")

    owner = db.query(OrganizationMember).filter_by(user_id=user.id, role="owner").first()
    if owner: raise HTTPException(400, "Organisationens ägare kan inte tas bort här.")
    db.delete(user)
    db.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Användaren finns inte")

    return templates.TemplateResponse(
        "users/edit.html",
        {
            "request": request,
            "current_user": current_user,
            "user": user,
        }
    )


@router.post("/users/{user_id}/edit")
async def edit_user(
    user_id: int,
    full_name: str = Form(""),
    email: str = Form(...),
    password: str = Form(""),
    is_superuser: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.organization_id == current_user.organization_id,
        )
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="Användaren finns inte")

    email = normalize_email(email)
    if not 1 <= len(full_name.strip()) <= 120: raise HTTPException(400, "Namn måste innehålla 1–120 tecken")
    existing_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.id != user_id,
        )
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    email_changed = user.email != email
    user.session_version += 1
    user.reset_token = None
    user.reset_token_expires_at = None
    if email_changed: user.email_verified = False
    user.full_name = full_name.strip()
    user.email = email.strip()

    # Eget konto ska inte kunna råka förlora admin via formuläret
    owner = db.query(OrganizationMember).filter_by(user_id=user.id, role="owner").first()
    if user.id != current_user.id and not owner:
        user.is_superuser = True if is_superuser else False

    # Ändra bara lösenord om något faktiskt skrivits in
    if password and password.strip():
        user.hashed_password = hash_password(password)

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == current_user.organization_id,
        )
        .first()
    )

    if membership:
        if membership.role != "owner":
            membership.role = "admin" if user.is_superuser else "member"

    db.commit()
    if not user.email_verified:
        await issue_verification(db, user)

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)