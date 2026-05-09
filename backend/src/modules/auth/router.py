from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.db.session import get_db
from src.models import StudentProfile, TeacherProfile, User
from src.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.modules.auth.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        status="active",
    )
    db.add(user)
    db.flush()

    if payload.role == "student":
        if not payload.student_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="student_code is required for student")
        code = payload.student_code.strip()
        existing_profile = db.query(StudentProfile).filter(StudentProfile.student_code == code).first()
        if existing_profile:
            if existing_profile.user_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This student_code is already registered. Use login or another code.",
                )
            existing_profile.user_id = user.id
            existing_profile.display_name = payload.display_name
            existing_profile.class_name = payload.class_name
            existing_profile.grade = payload.grade
        else:
            db.add(
                StudentProfile(
                    user_id=user.id,
                    student_code=code,
                    display_name=payload.display_name,
                    class_name=payload.class_name,
                    grade=payload.grade,
                )
            )
    else:
        db.add(
            TeacherProfile(
                user_id=user.id,
                display_name=payload.display_name,
                organization=payload.organization,
                subject=payload.subject,
            )
        )

    db.commit()

    access = create_token(str(user.id), user.role, "access", settings.access_token_expire_minutes)
    refresh = create_token(str(user.id), user.role, "refresh", settings.refresh_token_expire_minutes)
    return TokenResponse(access_token=access, refresh_token=refresh, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter(User.email == payload.email, User.status == "active").first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access = create_token(str(user.id), user.role, "access", settings.access_token_expire_minutes)
    refresh = create_token(str(user.id), user.role, "refresh", settings.refresh_token_expire_minutes)
    return TokenResponse(access_token=access, refresh_token=refresh, role=user.role)
