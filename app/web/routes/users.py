from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.templates import templates
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.models.user import User

router = APIRouter()


@router.get("/users", response_class=HTMLResponse)
def users_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Behörighet saknas")

    users = db.query(User).order_by(User.id.asc()).all()

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
        raise HTTPException(status_code=403)

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
        raise HTTPException(status_code=403)

    # check om user redan finns
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(password),
        is_superuser=True if is_superuser else False,
        is_active=True,
        organization_id=current_user.organization_id,  # viktigt!
    )

    db.add(user)
    db.commit()

    return RedirectResponse(url="/users", status_code=303)


@router.post("/users/{user_id}/delete")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403)

    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Kan inte ta bort dig själv")

    user = db.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User finns inte")

    db.delete(user)
    db.commit()

    return RedirectResponse(url="/users", status_code=303)


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
def edit_user_form(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403)

    user = db.get(User, user_id)
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
    is_active: str = Form(None),
    is_superuser: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403)

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Användaren finns inte")

    existing_user = db.query(User).filter(User.email == email, User.id != user_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-post finns redan")

    user.full_name = full_name
    user.email = email
    user.is_active = True if is_active else False
    user.is_superuser = True if is_superuser else False

    if password:
        user.hashed_password = hash_password(password)

    db.commit()

    return RedirectResponse(url="/users", status_code=303)