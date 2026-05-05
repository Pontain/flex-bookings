from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.templates import templates
from app.core.dependencies import get_current_user
from app.core.security import hash_password
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
def create_user(
    full_name: str = Form(""),
    email: str = Form(...),
    password: str = Form(...),
    is_superuser: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    user = User(
        full_name=full_name,
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
def edit_user(
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

    existing_user = (
        db.query(User)
        .filter(
            User.email == email,
            User.id != user_id,
            User.organization_id == current_user.organization_id,
        )
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    user.full_name = full_name.strip()
    user.email = email.strip()

    # Eget konto ska inte kunna råka förlora admin via formuläret
    if user.id != current_user.id:
        user.is_superuser = True if is_superuser else False

    # Ändra bara lösenord om något faktiskt skrivits in
    if password and password.strip():
        user.hashed_password = hash_password(password.strip())

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.user_id == user.id,
            OrganizationMember.organization_id == current_user.organization_id,
        )
        .first()
    )

    if membership:
        membership.role = "admin" if user.is_superuser else "member"

    db.commit()

    return RedirectResponse(url="/users", status_code=status.HTTP_303_SEE_OTHER)