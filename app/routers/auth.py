import os
import requests
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserRead
from app.services.security import verify_password, get_password_hash, create_access_token, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Authentication"])

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials 

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    """Dependency that ensures the current user is an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action."
        )
    return current_user


# --- Local Auth ---

@router.post("/signup", response_model=UserRead)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        hashed_password=hashed_pw,
        full_name=user.full_name,
        provider="local"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# --- Google Auth ---

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")


class GoogleToken(BaseModel):
    token: str

@router.post("/google/", response_model=Token)
def google_login_direct(payload: GoogleToken, db: Session = Depends(get_db)):
    # 1. Ask Google for the user's info using the token React sent us
    user_info_res = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={payload.token}")
    
    if user_info_res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")
    
    user_info = user_info_res.json()
    email = user_info.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="No email provided by Google")
    
    # 2. Check if the user already exists in our database
    user = db.query(User).filter(User.email == email).first()
    
    # 3. If they don't exist, create an account for them automatically
    if not user:
        user = User(
            email=email,
            full_name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 4. Generate our own backend JWT token and send it back to React
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/google/url")
def google_login_url():
    return {
        "url": f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={GOOGLE_REDIRECT_URI}&scope=openid%20profile%20email&access_type=offline"
    }

@router.get("/google/callback", response_model=Token)
def google_auth_callback(code: str, db: Session = Depends(get_db)):
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
    }
    res = requests.post(token_url, data=payload)
    if res.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to retrieve token from Google")
    
    tokens = res.json()
    
    user_info_res = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={tokens['access_token']}")
    user_info = user_info_res.json()
    
    email = user_info.get("email")
    
    # Check if user exists, else create
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        user = User(
            email=email,
            full_name=user_info.get("name"),
            picture=user_info.get("picture"),
            provider="google",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}