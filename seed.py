from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()

telegram_id = "123456789"

existing_user = db.query(User).filter(User.telegram_id == telegram_id).first()

if not existing_user:
    user = User(
        telegram_id=telegram_id,
        name="Test Worker",
        role="worker",
        is_active=True
    )
    db.add(user)
    db.commit()
    print("User created.")
else:
    print("User already exists.")

db.close()