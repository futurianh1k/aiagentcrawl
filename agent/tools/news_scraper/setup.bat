@echo off
chcp 65001 > nul
REM 2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
REM Windows 자동 설치 스크립트

echo 🚀 Playwright 기반 크롤링 파이프라인 설치 시작
echo ==================================================
echo.

REM Python 버전 확인
echo 📋 Python 버전 확인 중...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python이 설치되지 않았습니다.
    echo Python 3.10 이상을 설치하고 PATH에 추가한 후 다시 실행해주세요.
    echo Python 다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% 발견

REM Python 3.10+ 버전 확인
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.10 이상이 필요합니다. 현재 버전: %PYTHON_VERSION%
    pause
    exit /b 1
)
echo ✅ Python 버전 요구사항 충족 (3.10+)

REM 가상환경 생성
echo.
echo 📦 가상환경 생성 중...
if not exist "venv" (
    python -m venv venv
    echo ✅ 가상환경 생성 완료
) else (
    echo 📁 기존 가상환경 발견
)

REM 가상환경 활성화
echo.
echo 🔄 가상환경 활성화 중...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ 가상환경 활성화 실패
    pause
    exit /b 1
)
echo ✅ 가상환경 활성화 완료

REM pip 업그레이드
echo.
echo ⬆️ pip 업그레이드 중...
python -m pip install --upgrade pip
echo ✅ pip 업그레이드 완료

REM 의존성 패키지 설치
echo.
echo 📚 의존성 패키지 설치 중...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ 패키지 설치 실패
        pause
        exit /b 1
    )
    echo ✅ 패키지 설치 완료
) else (
    echo ❌ requirements.txt 파일을 찾을 수 없습니다.
    pause
    exit /b 1
)

REM Playwright 브라우저 설치
echo.
echo 🎭 Playwright 브라우저 설치 중...
playwright install chromium
if %errorlevel% neq 0 (
    echo ❌ Playwright 브라우저 설치 실패
    echo 수동으로 설치를 시도해보세요: playwright install chromium
    pause
    exit /b 1
)
echo ✅ Chromium 브라우저 설치 완료

REM 환경 변수 파일 생성
echo.
echo ⚙️ 환경 변수 파일 설정 중...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ .env 파일 생성 완료 (.env.example에서 복사)
        echo ⚠️ .env 파일을 편집하여 데이터베이스 설정을 완료하세요
    ) else (
        echo ❌ .env.example 파일을 찾을 수 없습니다.
    )
) else (
    echo 📁 기존 .env 파일 발견
)

REM 로그 디렉토리 생성
echo.
echo 📁 로그 디렉토리 생성 중...
if not exist "logs" mkdir logs
echo ✅ 로그 디렉토리 생성 완료

REM 데이터베이스 연결 테스트 (선택적)
echo.
echo 🗄️ 데이터베이스 연결 테스트...
python -c "try: from models.database import test_connection; print('✅ 데이터베이스 연결 성공' if test_connection() else '⚠️ 데이터베이스 연결 실패 - .env 파일에서 DB 설정을 확인하세요'); except Exception as e: print(f'⚠️ 데이터베이스 테스트 건너뛰기: {e}')" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ 데이터베이스 설정을 나중에 완료하세요
)

REM 설치 완료 메시지
echo.
echo 🎉 설치가 성공적으로 완료되었습니다!
echo ==================================================
echo.
echo 📋 다음 단계:
echo 1. .env 파일 편집: notepad .env
echo 2. 데이터베이스 설정 완료
echo 3. 가상환경 활성화: venv\Scripts\activate.bat
echo 4. 예제 실행: python examples\01_playwright_setup.py
echo.
echo 📚 도움말:
echo - README.md 파일을 참조하세요
echo - 문제 발생시 GitHub Issues에 신고하세요
echo.
echo 해피 크롤링! 🕷️
echo.
pause
