from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.services.audit_service import log_action
from app.limiter import limiter

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
    to_encode["iss"] = "hanz-learning-companion"
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _user_token_claims(user: User, token_type: str) -> dict:
    """Bind tokens to both user id and email so recycled numeric IDs cannot impersonate."""
    return {
        "sub": str(user.id),
        "email": user.email.lower(),
        "type": token_type,
    }


def _resolve_user_from_payload(payload: dict, db: Session, *, expected_type: str) -> User:
    user_id = payload.get("sub")
    token_type = payload.get("type")
    email = payload.get("email")
    if user_id is None or token_type != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token")
    # Reject legacy tokens that only had a numeric sub (unsafe after DB resets).
    if not email or not isinstance(email, str):
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if user.email.lower() != email.lower():
        raise HTTPException(status_code=401, detail="Session expired — please sign in again")
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return _resolve_user_from_payload(payload, db, expected_type="access")
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=UserResponse)
@limiter.limit("5/minute")
def register(request: Request, data: UserRegister, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        hashed_password=_hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    db.flush()
    log_action(
        db,
        "user_registered",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    email = data.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Fallback for older rows that may not be lowercased
        user = db.query(User).filter(User.email == data.email.strip()).first()
    if not user or not _verify_password(data.password, user.hashed_password):
        log_action(
            db,
            "login_failed",
            ip_address=request.client.host if request.client else None,
            details={"email": data.email},
        )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    settings = get_settings()
    access_token = _create_token(
        _user_token_claims(user, "access"),
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = _create_token(
        _user_token_claims(user, "refresh"),
        timedelta(days=settings.refresh_token_expire_days),
    )
    log_action(
        db,
        "login_success",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh(request: Request, data: TokenRefresh, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        payload = jwt.decode(
            data.refresh_token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user = _resolve_user_from_payload(payload, db, expected_type="refresh")
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access_token = _create_token(
        _user_token_claims(user, "access"),
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = _create_token(
        _user_token_claims(user, "refresh"),
        timedelta(days=settings.refresh_token_expire_days),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
