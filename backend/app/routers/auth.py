from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, TokenRefresh, UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def _create_token(data: dict, expires_delta: timedelta) -> str:
    settings = get_settings()
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        token_type: str = payload.get("type", "access")
        if user_id is None or token_type != "access":
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = int(user_id)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=UserResponse)
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=_hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not _verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings()
    access_token = _create_token(
        {"sub": str(user.id), "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = _create_token(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: TokenRefresh, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        payload = jwt.decode(data.refresh_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        token_type: str = payload.get("type")
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = int(user_id)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access_token = _create_token(
        {"sub": str(user.id), "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = _create_token(
        {"sub": str(user.id), "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
