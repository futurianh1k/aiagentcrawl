"""
인증 관련 API 라우터
회원 가입, 로그인, 토큰 관리, 이메일 인증 등
한국 정부 IT 보안 규정 준수
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_verification_token,
    is_account_locked,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.database import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    EmailVerification,
    MessageResponse
)

router = APIRouter()
security = HTTPBearer()

# 계정 잠금 설정
MAX_LOGIN_ATTEMPTS = 5  # 최대 로그인 시도 횟수
ACCOUNT_LOCK_DURATION_MINUTES = 30  # 계정 잠금 시간 (분)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    회원 가입

    - **email**: 이메일 주소 (고유값, 필수)
    - **password**: 비밀번호 (8자 이상, 영문+숫자+특수문자 조합, 필수)
    - **full_name**: 이름 (선택)

    한국 정부 IT 보안 규정:
    - 비밀번호 복잡도 검증
    - bcrypt 해싱
    - SQL Injection 방지 (SQLAlchemy ORM)
    - XSS 방지 (입력값 정제)
    """
    # 기존 사용자 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다."
        )

    try:
        # 이메일 인증 토큰 생성
        verification_token = generate_verification_token()
        verification_expires = datetime.utcnow() + timedelta(hours=24)

        # 새 사용자 생성
        new_user = User(
            email=user_data.email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            email_verification_token=verification_token,
            email_verification_token_expires=verification_expires,
            is_verified=False  # 이메일 인증 필요
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # TODO: 이메일 인증 링크 전송
        # 실제 운영 환경에서는 이메일을 전송해야 함
        # send_verification_email(user_data.email, verification_token)

        return MessageResponse(
            message="회원 가입이 완료되었습니다.",
            detail=f"이메일 인증을 완료해주세요. (개발 환경: 인증 토큰 = {verification_token})"
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="회원 가입 중 오류가 발생했습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    """
    로그인

    - **email**: 이메일 주소
    - **password**: 비밀번호

    보안 기능:
    - 로그인 실패 횟수 추적
    - 계정 자동 잠금 (5회 실패 시 30분 잠금)
    - JWT 토큰 발급
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 계정 활성화 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다. 관리자에게 문의하세요."
        )

    # 계정 잠금 확인
    if is_account_locked(user.locked_until):
        lock_time_remaining = (user.locked_until.replace(tzinfo=None) - datetime.utcnow()).seconds // 60
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"계정이 잠겼습니다. {lock_time_remaining}분 후에 다시 시도하세요."
        )

    # 비밀번호 검증
    if not verify_password(credentials.password, user.hashed_password):
        # 로그인 실패 횟수 증가
        user.failed_login_attempts += 1

        # 최대 시도 횟수 초과 시 계정 잠금
        if user.failed_login_attempts >= MAX_LOGIN_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=ACCOUNT_LOCK_DURATION_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"로그인 {MAX_LOGIN_ATTEMPTS}회 실패로 계정이 {ACCOUNT_LOCK_DURATION_MINUTES}분간 잠겼습니다."
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 이메일 인증 확인 (선택적)
    # if not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="이메일 인증을 완료해주세요."
    #     )

    # 로그인 성공 - 실패 횟수 초기화
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    db.commit()

    # JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # 초 단위로 변환
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Session = Depends(get_db)
):
    """
    액세스 토큰 갱신

    - **refresh_token**: 리프레시 토큰
    """
    # 리프레시 토큰 검증
    payload = verify_token(token_data.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    # 사용자 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자입니다."
        )

    # 새 액세스 토큰 생성
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    # 새 리프레시 토큰 생성
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )

    return Token(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    verification_data: EmailVerification,
    db: Session = Depends(get_db)
):
    """
    이메일 인증

    - **token**: 이메일 인증 토큰
    """
    # 토큰으로 사용자 조회
    user = db.query(User).filter(
        User.email_verification_token == verification_data.token
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효하지 않은 인증 토큰입니다."
        )

    # 토큰 만료 확인
    if user.email_verification_token_expires and \
       datetime.utcnow() > user.email_verification_token_expires.replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증 토큰이 만료되었습니다. 새로운 인증 이메일을 요청하세요."
        )

    # 이메일 인증 완료
    user.is_verified = True
    user.email_verification_token = None
    user.email_verification_token_expires = None
    db.commit()

    return MessageResponse(
        message="이메일 인증이 완료되었습니다.",
        detail="이제 모든 기능을 사용하실 수 있습니다."
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    현재 로그인한 사용자 정보 조회

    - **Authorization**: Bearer 토큰 (헤더)
    """
    # 토큰 검증
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다."
        )

    # 사용자 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )

    return user
