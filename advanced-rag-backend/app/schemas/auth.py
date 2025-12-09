from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class RegisterResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    created_at: datetime
