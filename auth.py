"""
This file handles two separate concerns:
1. Password hashing (never store plain-text passwords)
2. JWT creation and verification (proving who a user is on later requests)
"""

import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_dev_secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# CryptContext handles hashing with bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPBearer makes the /docs "Authorize" button just ask for a raw token
# string to paste in, rather than trying to run its own login form.
bearer_scheme = HTTPBearer()


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Packs data (we'll put the user's id in here) into a signed JWT string
    that expires after JWT_EXPIRE_MINUTES.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    This is a FastAPI "dependency". Any endpoint that adds
    `current_user: User = Depends(get_current_user)` as a parameter will
    automatically require a valid JWT token, and will get back the actual
    User object for whoever is making the request.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Same idea as get_current_user, but also checks the role is admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user