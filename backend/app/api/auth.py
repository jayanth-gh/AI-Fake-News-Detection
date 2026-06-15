import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

from app.db.database import get_db
from app.db import models
from app.schemas import schemas
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "demo")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "demo1234")


def ensure_default_user(db: Session):
    existing_user = db.query(models.User).filter(models.User.username == DEFAULT_USERNAME).first()
    if existing_user:
        return existing_user

    new_user = models.User(
        username=DEFAULT_USERNAME,
        hashed_password=get_password_hash(DEFAULT_PASSWORD),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str):
    if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
        return ensure_default_user(db)

    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not user.hashed_password:
        return None

    try:
        if not verify_password(password, user.hashed_password):
            return None
    except Exception as exc:
        print(f"Password verification failed for {username}: {exc}")
        return None

    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(models.User).filter(models.User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Username already registered")

        safe_password = user.password[:72]
        hashed_password = get_password_hash(safe_password)

        new_user = models.User(
            username=user.username,
            hashed_password=hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except HTTPException:
        raise
    except Exception as exc:
        print(f"Registration failed: {exc}")
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.") from exc


@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
