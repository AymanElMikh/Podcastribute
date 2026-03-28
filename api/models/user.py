"""Pydantic models for user authentication and account management."""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Request body for new user registration."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public-facing user data returned from API responses."""

    id: str
    email: str
    plan: str
    episodes_this_month: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """JWT token response returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
