"""
보안 관련 함수 모듈

보안 가이드라인에 따른 보안 관련 함수들을 제공합니다.
"""

import re
from typing import Any, Dict, Optional


def mask_sensitive_data(data: Any, mask_char: str = "*") -> Any:
    """
    민감한 데이터 마스킹
    
    보안 가이드라인: 로그, 예외 메시지에 민감한 정보를 포함하지 않습니다.
    
    Args:
        data: 마스킹할 데이터
        mask_char: 마스킹 문자
    
    Returns:
        마스킹된 데이터
    """
    if isinstance(data, str):
        # API 키 패턴 마스킹 (sk-로 시작하는 경우)
        if data.startswith("sk-") and len(data) > 10:
            return data[:7] + mask_char * (len(data) - 10) + data[-3:]

        # 긴 문자열은 일부만 표시
        if len(data) > 20:
            return data[:5] + mask_char * 10 + data[-5:]

    elif isinstance(data, dict):
        masked = {}
        sensitive_keys = ["key", "password", "secret", "token", "api_key", "auth", "credential"]

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked[key] = mask_sensitive_data(value, mask_char)
            else:
                masked[key] = value

        return masked

    elif isinstance(data, list):
        return [mask_sensitive_data(item, mask_char) for item in data]

    return data


def validate_api_key(api_key: Optional[str], key_type: str = "OpenAI") -> bool:
    """
    API 키 검증
    
    Args:
        api_key: 검증할 API 키
        key_type: API 키 타입
    
    Returns:
        유효한 API 키 여부
    """
    if not api_key:
        return False

    if not isinstance(api_key, str):
        return False

    if len(api_key) < 10:
        return False

    # OpenAI API 키는 sk-로 시작
    if key_type == "OpenAI" and not api_key.startswith("sk-"):
        return False

    return True


def sanitize_filename(filename: str) -> str:
    """
    파일명 정제 (경로 공격 방지)
    
    보안 가이드라인: 사용자가 올린 파일명을 그대로 사용하지 않습니다.
    
    Args:
        filename: 정제할 파일명
    
    Returns:
        정제된 파일명
    """
    if not isinstance(filename, str):
        return "file"

    # 경로 구분자 제거
    filename = filename.replace("/", "_").replace("\\", "_")

    # 위험한 문자 제거
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

    # 빈 문자열 처리
    if not filename:
        return "file"

    # 너무 긴 파일명 처리
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def check_sql_injection(text: str) -> bool:
    """
    SQL Injection 패턴 검사
    
    Args:
        text: 검사할 텍스트
    
    Returns:
        SQL Injection 패턴 발견 여부
    """
    if not isinstance(text, str):
        return False

    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(\bUNION\b.*\bSELECT\b)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def check_xss_pattern(text: str) -> bool:
    """
    XSS 패턴 검사
    
    Args:
        text: 검사할 텍스트
    
    Returns:
        XSS 패턴 발견 여부
    """
    if not isinstance(text, str):
        return False

    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]

    for pattern in xss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False

