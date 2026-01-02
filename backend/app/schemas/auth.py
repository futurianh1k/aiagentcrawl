"""
인증 관련 Pydantic 스키마
회원가입, 로그인, 토큰 등
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from app.core.security import validate_password_strength, sanitize_email


class UserRegister(BaseModel):
    """회원 가입 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호")
    full_name: Optional[str] = Field(None, max_length=100, description="이름")

    @validator('email')
    def validate_email(cls, v):
        """이메일 검증 및 정제"""
        return sanitize_email(v)

    @validator('password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

    @validator('full_name')
    def validate_full_name(cls, v):
        """이름 검증 (XSS 방지)"""
        if v is not None:
            # HTML 태그 제거
            import re
            v = re.sub(r'<[^>]*>', '', v)
            v = v.strip()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ssw0rd!",
                "full_name": "홍길동"
            }
        }


class UserLogin(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")

    @validator('email')
    def validate_email(cls, v):
        """이메일 정제"""
        return sanitize_email(v)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecureP@ssw0rd!"
            }
        }


class Token(BaseModel):
    """JWT 토큰 응답 스키마"""
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    expires_in: int = Field(..., description="만료 시간 (초)")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class TokenRefresh(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str = Field(..., description="리프레시 토큰")

    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class UserResponse(BaseModel):
    """사용자 정보 응답 스키마"""
    id: int
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "email": "user@example.com",
                "full_name": "홍길동",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login_at": "2024-01-02T12:00:00Z"
            }
        }


class EmailVerification(BaseModel):
    """이메일 인증 요청 스키마"""
    token: str = Field(..., description="인증 토큰")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456ghi789..."
            }
        }


class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr = Field(..., description="이메일 주소")

    @validator('email')
    def validate_email(cls, v):
        """이메일 정제"""
        return sanitize_email(v)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class PasswordReset(BaseModel):
    """비밀번호 재설정 스키마"""
    token: str = Field(..., description="재설정 토큰")
    new_password: str = Field(..., min_length=8, max_length=128, description="새 비밀번호")

    @validator('new_password')
    def validate_password(cls, v):
        """비밀번호 강도 검증"""
        is_valid, error_message = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error_message)
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456ghi789...",
                "new_password": "NewSecureP@ssw0rd!"
            }
        }


class MessageResponse(BaseModel):
    """일반 메시지 응답 스키마"""
    message: str = Field(..., description="응답 메시지")
    detail: Optional[str] = Field(None, description="상세 정보")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "회원 가입이 완료되었습니다.",
                "detail": "이메일 인증을 완료해주세요."
            }
        }
