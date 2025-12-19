"""
유틸리티 함수 모듈

공통으로 사용하는 유틸리티 함수들을 제공합니다.
"""

import logging
import re
from typing import Any, Optional
from datetime import datetime

# 로거 설정
logger = logging.getLogger(__name__)


def safe_log(message: str, level: str = "info", **kwargs) -> None:
    """
    안전한 로깅 함수
    
    보안 가이드라인: 민감한 정보(API 키, 비밀번호 등)는 로그에 기록하지 않습니다.
    
    Args:
        message: 로그 메시지
        level: 로그 레벨 (info, warning, error, debug)
        **kwargs: 추가 정보 (민감한 정보는 자동으로 마스킹됨)
    """
    # 민감한 정보 키워드
    sensitive_keys = ["key", "password", "secret", "token", "api_key", "auth"]

    # 민감한 정보 마스킹
    safe_kwargs = {}
    for key, value in kwargs.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            safe_kwargs[key] = "***MASKED***"
        else:
            safe_kwargs[key] = value

    log_message = f"{message}"
    if safe_kwargs:
        log_message += f" | {safe_kwargs}"

    if level == "info":
        logger.info(log_message)
    elif level == "warning":
        logger.warning(log_message)
    elif level == "error":
        logger.error(log_message)
    elif level == "debug":
        logger.debug(log_message)


def validate_input(text: str, max_length: int = 1000, min_length: int = 1) -> bool:
    """
    사용자 입력 검증
    
    보안 가이드라인: 모든 사용자 입력은 검증해야 합니다.
    
    Args:
        text: 검증할 텍스트
        max_length: 최대 길이
        min_length: 최소 길이
    
    Returns:
        검증 통과 여부
    """
    if not isinstance(text, str):
        return False

    if len(text) < min_length:
        return False

    if len(text) > max_length:
        return False

    # SQL Injection 방지 (기본적인 패턴)
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    return True


def sanitize_text(text: str) -> str:
    """
    텍스트 정제 (XSS 방지)
    
    보안 가이드라인: HTML 출력 시 값은 escape/encode 해야 합니다.
    
    Args:
        text: 정제할 텍스트
    
    Returns:
        정제된 텍스트
    """
    if not isinstance(text, str):
        return ""

    # HTML 특수 문자 이스케이프
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")

    return text


def validate_url(url: str) -> bool:
    """
    URL 검증
    
    Args:
        url: 검증할 URL
    
    Returns:
        유효한 URL 여부
    """
    if not isinstance(url, str):
        return False

    # 기본적인 URL 패턴 검증
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def format_datetime(dt: Optional[datetime] = None) -> str:
    """
    날짜 시간 포맷팅
    
    Args:
        dt: 날짜 시간 객체 (None이면 현재 시간)
    
    Returns:
        포맷된 문자열
    """
    if dt is None:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    텍스트 자르기
    
    Args:
        text: 자를 텍스트
        max_length: 최대 길이
        suffix: 접미사
    
    Returns:
        잘린 텍스트
    """
    if not isinstance(text, str):
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix

