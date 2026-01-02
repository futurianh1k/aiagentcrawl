"""
보안 유틸리티 모듈
비밀번호 해싱, JWT 토큰 생성/검증 등
한국 정부 IT 보안 규정 준수
"""

import secrets
import re
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# bcrypt를 사용한 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    비밀번호 강도 검증 - 한국 정부 IT 보안 규정 준수

    규정:
    - 최소 8자 이상
    - 영문 대소문자, 숫자, 특수문자 중 3가지 이상 조합
    - 연속된 문자 3개 이상 금지 (예: abc, 123)
    - 동일 문자 3개 이상 연속 금지 (예: aaa, 111)

    Returns:
        tuple[bool, Optional[str]]: (유효성, 에러 메시지)
    """
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."

    if len(password) > 128:
        return False, "비밀번호는 최대 128자까지 가능합니다."

    # 문자 종류 체크
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]', password))

    char_types = sum([has_upper, has_lower, has_digit, has_special])

    if char_types < 3:
        return False, "비밀번호는 영문 대소문자, 숫자, 특수문자 중 3가지 이상을 조합해야 합니다."

    # 연속된 문자 체크
    for i in range(len(password) - 2):
        # 연속된 숫자 체크 (예: 123, 234)
        if password[i:i+3].isdigit():
            if int(password[i+1]) == int(password[i]) + 1 and int(password[i+2]) == int(password[i]) + 2:
                return False, "연속된 숫자 3개 이상은 사용할 수 없습니다."

        # 연속된 알파벳 체크 (예: abc, ABC)
        if password[i:i+3].isalpha():
            if (ord(password[i+1]) == ord(password[i]) + 1 and
                ord(password[i+2]) == ord(password[i]) + 2):
                return False, "연속된 알파벳 3개 이상은 사용할 수 없습니다."

        # 동일 문자 반복 체크 (예: aaa, 111)
        if password[i] == password[i+1] == password[i+2]:
            return False, "동일한 문자 3개 이상 연속으로 사용할 수 없습니다."

    return True, None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성

    Args:
        data: 토큰에 포함할 데이터
        expires_delta: 만료 시간 (기본값: 30분)

    Returns:
        str: JWT 토큰
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    JWT 리프레시 토큰 생성

    Args:
        data: 토큰에 포함할 데이터

    Returns:
        str: JWT 리프레시 토큰
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        Optional[dict]: 토큰 페이로드 또는 None
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_verification_token() -> str:
    """
    이메일 인증용 보안 토큰 생성

    Returns:
        str: 32바이트 랜덤 토큰 (URL-safe)
    """
    return secrets.token_urlsafe(32)


def generate_reset_token() -> str:
    """
    비밀번호 재설정용 보안 토큰 생성

    Returns:
        str: 32바이트 랜덤 토큰 (URL-safe)
    """
    return secrets.token_urlsafe(32)


def sanitize_email(email: str) -> str:
    """
    이메일 주소 정제 (XSS 방지)

    Args:
        email: 이메일 주소

    Returns:
        str: 정제된 이메일 주소
    """
    return email.lower().strip()


def is_account_locked(locked_until: Optional[datetime]) -> bool:
    """
    계정 잠금 상태 확인

    Args:
        locked_until: 계정 잠금 해제 시간

    Returns:
        bool: 잠금 여부
    """
    if locked_until is None:
        return False

    return datetime.utcnow() < locked_until.replace(tzinfo=None)
