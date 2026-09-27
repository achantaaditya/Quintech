from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

password_hash = PasswordHash.recommended()
bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    return password_hash.hash(password)

def verify_password(password: str, value: str) -> bool:
    return password_hash.verify(password, value)

def create_token(user_id: int, refresh: bool = False) -> str:
    exp = timedelta(days=14) if refresh else timedelta(minutes=settings.access_token_minutes)
    secret = settings.jwt_refresh_secret if refresh else settings.jwt_secret
    return jwt.encode({"sub": str(user_id), "type": "refresh" if refresh else "access", "exp": datetime.now(timezone.utc) + exp}, secret, algorithm="HS256")

def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
        if payload.get("type") != "access": raise ValueError
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    if not user: raise HTTPException(status_code=404, detail="User not found")
    return user
