from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import hash_password


def create_user():
    try:
        email = TypeAdapter(EmailStr).validate_python(
            input("Enter lab member email: ").strip()
        ).lower()
    except ValidationError:
        print("Invalid email address.")
        return

    password = getpass("Enter password: ")
    confirm_password = getpass("Confirm password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print("A user with this email already exists.")
            return

        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_active=True
        )

        db.add(user)
        db.commit()

        print(f"Account created successfully for {email}")


if __name__ == "__main__":
    create_user()