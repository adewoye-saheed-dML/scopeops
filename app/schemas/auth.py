from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    picture: Optional[str] = None
    provider: str

    class Config:
        from_attributes = True