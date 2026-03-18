# scripts/seed_admin.py
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def main():
    db = SessionLocal()

    existing_user = db.query(User).filter(User.email == "admin@example.com").first()
    if existing_user:
        print("Admin-användare finns redan.")
        db.close()
        return

    user = User(
        organization_id=1,
        email="admin@example.com",
        full_name="Admin",
        hashed_password=hash_password("byt-det-har-losenordet"),
        is_active=True,
        is_superuser=True,
    )

    db.add(user)
    db.commit()
    db.close()

    print("Admin-användare skapad.")


if __name__ == "__main__":
    main()