from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models import PatientProfile, User, UserRole
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.audit_logger import log_security_event
from app.security.rate_limit import check_rate_limit, ip_key

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, ip_key(request), 5, 60)
    email = payload.email.lower()
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        log_security_event(
            db,
            action="register_duplicate_email",
            resource_type="auth",
            request=request,
            metadata={"email": email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.patient,
    )
    db.add(user)
    db.flush()
    db.add(PatientProfile(user_id=user.id))
    db.commit()
    db.refresh(user)
    log_security_event(
        db,
        action="register_success",
        resource_type="auth",
        request=request,
        user_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
    )
    db.commit()
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    check_rate_limit(request, ip_key(request), 5, 60)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        log_security_event(
            db,
            action="login_failure",
            resource_type="auth",
            request=request,
            user_id=user.id if user else None,
            metadata={"email": payload.email.lower()},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    log_security_event(
        db,
        action="login_success",
        resource_type="auth",
        request=request,
        user_id=user.id,
        metadata={"email": user.email, "role": user.role.value},
    )
    db.commit()
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
