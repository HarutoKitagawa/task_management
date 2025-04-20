from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from ..database import get_db
from ..models import User
from .schemas import UserCreate, SignupOut, LoginOut
from .utils import get_password_hash, verify_password, create_access_token
from .dependencies import get_user

from datetime import timedelta

ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter()

@router.post("/signup", response_model=SignupOut)
def signup(user_create: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_create.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user_create.password)
    new_user = User(
        username=user_create.username,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return SignupOut.model_validate(new_user)

@router.post("/login", response_model=LoginOut)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.username, access_token_expires)
    return LoginOut(
        id=user.id,
        username=user.username,
        access_token=access_token,
        token_type="bearer"
    )
