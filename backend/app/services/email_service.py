"""
이메일 전송 서비스
회원 가입, 이메일 인증, 비밀번호 재설정 등
"""

import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    이메일 전송

    Args:
        to_email: 수신자 이메일
        subject: 제목
        html_content: HTML 내용
        text_content: 텍스트 내용 (선택)

    Returns:
        bool: 전송 성공 여부
    """
    # SMTP 설정이 없으면 로그만 출력
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            f"SMTP 설정이 없어 이메일을 전송하지 않았습니다. "
            f"수신자: {to_email}, 제목: {subject}"
        )
        return False

    try:
        # 이메일 메시지 생성
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject

        # 텍스트 내용 추가
        if text_content:
            part1 = MIMEText(text_content, "plain")
            message.attach(part1)

        # HTML 내용 추가
        part2 = MIMEText(html_content, "html")
        message.attach(part2)

        # SMTP 서버 연결 및 전송
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )

        logger.info(f"이메일 전송 성공: {to_email}")
        return True

    except Exception as e:
        logger.error(f"이메일 전송 실패: {to_email}, 오류: {str(e)}")
        return False


async def send_verification_email(
    to_email: str,
    verification_token: str
) -> bool:
    """
    이메일 인증 메일 전송

    Args:
        to_email: 수신자 이메일
        verification_token: 인증 토큰

    Returns:
        bool: 전송 성공 여부
    """
    verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={verification_token}"

    subject = "이메일 인증을 완료해주세요"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>이메일 인증</h2>
            <p>안녕하세요,</p>
            <p>News Sentiment AI Agent System에 가입해주셔서 감사합니다.</p>
            <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요:</p>
            <a href="{verification_url}" class="button">이메일 인증하기</a>
            <p>또는 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
            <p style="word-break: break-all; color: #007bff;">{verification_url}</p>
            <p>이 링크는 24시간 동안 유효합니다.</p>
            <div class="footer">
                <p>본 메일은 발신 전용입니다. 문의사항이 있으시면 고객센터로 연락해주세요.</p>
                <p>&copy; 2024 News Sentiment AI Agent System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    이메일 인증

    안녕하세요,

    News Sentiment AI Agent System에 가입해주셔서 감사합니다.

    아래 링크를 클릭하여 이메일 인증을 완료해주세요:
    {verification_url}

    이 링크는 24시간 동안 유효합니다.

    본 메일은 발신 전용입니다.
    © 2024 News Sentiment AI Agent System. All rights reserved.
    """

    return await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(
    to_email: str,
    reset_token: str
) -> bool:
    """
    비밀번호 재설정 메일 전송

    Args:
        to_email: 수신자 이메일
        reset_token: 재설정 토큰

    Returns:
        bool: 전송 성공 여부
    """
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"

    subject = "비밀번호 재설정 요청"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #dc3545;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .warning {{
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>비밀번호 재설정</h2>
            <p>안녕하세요,</p>
            <p>비밀번호 재설정 요청을 받았습니다.</p>
            <p>아래 버튼을 클릭하여 새 비밀번호를 설정해주세요:</p>
            <a href="{reset_url}" class="button">비밀번호 재설정하기</a>
            <p>또는 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
            <p style="word-break: break-all; color: #dc3545;">{reset_url}</p>
            <div class="warning">
                <strong>⚠️ 보안 주의사항</strong>
                <ul>
                    <li>본인이 요청하지 않은 경우 이 메일을 무시하세요.</li>
                    <li>이 링크는 1시간 동안만 유효합니다.</li>
                    <li>비밀번호는 8자 이상, 영문+숫자+특수문자를 포함해야 합니다.</li>
                </ul>
            </div>
            <div class="footer">
                <p>본 메일은 발신 전용입니다. 문의사항이 있으시면 고객센터로 연락해주세요.</p>
                <p>&copy; 2024 News Sentiment AI Agent System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    비밀번호 재설정

    안녕하세요,

    비밀번호 재설정 요청을 받았습니다.

    아래 링크를 클릭하여 새 비밀번호를 설정해주세요:
    {reset_url}

    ⚠️ 보안 주의사항:
    - 본인이 요청하지 않은 경우 이 메일을 무시하세요.
    - 이 링크는 1시간 동안만 유효합니다.
    - 비밀번호는 8자 이상, 영문+숫자+특수문자를 포함해야 합니다.

    본 메일은 발신 전용입니다.
    © 2024 News Sentiment AI Agent System. All rights reserved.
    """

    return await send_email(to_email, subject, html_content, text_content)


async def send_welcome_email(
    to_email: str,
    full_name: Optional[str] = None
) -> bool:
    """
    환영 메일 전송 (이메일 인증 완료 후)

    Args:
        to_email: 수신자 이메일
        full_name: 사용자 이름 (선택)

    Returns:
        bool: 전송 성공 여부
    """
    greeting = f"{full_name}님" if full_name else "회원님"
    subject = "가입을 환영합니다!"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>환영합니다!</h2>
            <p>{greeting},</p>
            <p>News Sentiment AI Agent System 가입을 축하합니다!</p>
            <p>이제 다양한 뉴스 감정 분석 서비스를 이용하실 수 있습니다.</p>
            <a href="{settings.FRONTEND_URL}" class="button">시작하기</a>
            <div class="footer">
                <p>문의사항이 있으시면 언제든지 연락주세요.</p>
                <p>&copy; 2024 News Sentiment AI Agent System. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """

    text_content = f"""
    환영합니다!

    {greeting},

    News Sentiment AI Agent System 가입을 축하합니다!

    이제 다양한 뉴스 감정 분석 서비스를 이용하실 수 있습니다.

    시작하기: {settings.FRONTEND_URL}

    문의사항이 있으시면 언제든지 연락주세요.
    © 2024 News Sentiment AI Agent System. All rights reserved.
    """

    return await send_email(to_email, subject, html_content, text_content)
