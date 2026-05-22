from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from household_manager.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from household_manager.database import get_db
from household_manager.models.user import DBUser
from household_manager.schemas.auth import LoginRequest, Token, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.execute(
        select(DBUser).where(DBUser.username == user.username)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    db_user = DBUser(
        username=user.username, password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
async def login_user(credentials: LoginRequest, db: Session = Depends(get_db)):
    db_user = db.execute(
        select(DBUser).where(DBUser.username == credentials.username)
    ).scalar_one_or_none()

    if not db_user or not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(subject=db_user.username)
    return Token(access_token=access_token)
