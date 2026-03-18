from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def main():
    db = SessionLocal()

    email = "admin@example.com"
    password = "admin123"  # 👈 här sätter du lösenordet

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print("Admin finns redan")
        db.close()
        return

    user = User(
        organization_id=1,
        email=email,
        full_name="Admin",
        hashed_password=hash_password(password),  # 👈 hash sker här
        is_active=True,
        is_superuser=True,
    )

    db.add(user)
    db.commit()
    db.close()

    print("Admin skapad!")


if __name__ == "__main__":
    main()