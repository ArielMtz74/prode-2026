from models import SessionLocal, User
from auth import hash_password

db = SessionLocal()
user = db.query(User).filter(User.username == "Ariel").first()
if user:
    user.password_hash = hash_password("123456")
    db.commit()
    print("Password reset successfully for Ariel to '123456'")
else:
    print("User Ariel not found.")
db.close()
