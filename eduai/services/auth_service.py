import os
import json
import bcrypt
from eduai.database.connection import SessionLocal
from eduai.database.models import User, UserRole

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".studyflow_session.json")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    @classmethod
    def register_user(cls, username, email, password, role_enum):
        db = SessionLocal()
        try:
            # Check username
            if db.query(User).filter(User.username == username).first():
                return False, "Username already exists."
            # Check email
            if db.query(User).filter(User.email == email).first():
                return False, "Email already exists."
            
            pwd_hash = cls.hash_password(password)
            user = User(
                username=username,
                email=email,
                password_hash=pwd_hash,
                role=role_enum,
                xp=0,
                level=1,
                streak_count=1
            )
            db.add(user)
            db.commit()
            return True, "Account registered successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Database Error: {str(e)}"
        finally:
            db.close()

    @classmethod
    def authenticate(cls, username, password, remember_me=False):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if user and cls.verify_password(password, user.password_hash):
                user_data = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "xp": user.xp,
                    "level": user.level,
                    "streak_count": user.streak_count
                }
                if remember_me:
                    cls.save_session(user_data)
                return user_data
            return None
        finally:
            db.close()

    @classmethod
    def reset_password(cls, username, email, new_password):
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username, User.email == email).first()
            if not user:
                return False, "User not found with matching username and email."
            
            user.password_hash = cls.hash_password(new_password)
            db.commit()
            return True, "Password reset successfully!"
        except Exception as e:
            db.rollback()
            return False, f"Error resetting password: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def save_session(user_data):
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(user_data, f)
        except Exception:
            pass

    @staticmethod
    def get_saved_session():
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    @staticmethod
    def clear_session():
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass
