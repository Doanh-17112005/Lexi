"""
Authentication Schemas
"""

import re
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_password_strength(value: str) -> str:
    """Apply one password policy to registration and password updates."""
    if len(value) < 8 or len(value) > 100:
        raise ValueError('Password must be between 8 and 100 characters')
    if not re.search(r'[A-Z]', value):
        raise ValueError('Password must contain at least 1 uppercase letter')
    if not re.search(r'[a-z]', value):
        raise ValueError('Password must contain at least 1 lowercase letter')
    if not re.search(r'[0-9]', value):
        raise ValueError('Password must contain at least 1 number')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/~`]', value):
        raise ValueError('Password must contain at least 1 special character')
    return value


class RegisterRequest(BaseModel):
    """Registration request."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    display_name: Optional[str] = None

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9._-]+$', v):
            raise ValueError(
                'Username may only contain letters (a-z, A-Z), digits, dots, underscores, or hyphens'
            )
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    """Login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    """Login response with user info."""
    user_id: str
    username: str
    email: str
    role: Optional[str] = "user"  # Role slug: user, admin, super_admin


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class LogoutRequest(BaseModel):
    """Logout request."""
    refresh_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


# ===== New schemas for missing endpoints =====

class GoogleLoginRequest(BaseModel):
    """Google OAuth login request."""
    id_token: str = Field(..., description="Google ID token from client")
    source: Literal["app", "admin"] = Field(default="app", description="Login source: 'app' for Flutter, 'admin' for web admin")

class FacebookLoginRequest(BaseModel):
    """Facebook login request (via Firebase)."""
    id_token: str = Field(..., description="Firebase ID token from client")
    source: Literal["app", "admin"] = Field(default="app", description="Login source: 'app' for Flutter, 'admin' for web admin")


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password with token."""
    token: str = Field(..., description="Password reset token from email")
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_new_password_strength(cls, v: str) -> str:
        return validate_password_strength(v)


class VerifyEmailRequest(BaseModel):
    """Verify email with token."""
    token: str = Field(..., description="Email verification token")


class VerifyEmailResponse(BaseModel):
    """Verify email response."""
    verified: bool
    message: str

