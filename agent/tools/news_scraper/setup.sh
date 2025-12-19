#!/bin/bash

# 2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
# Linux/Mac 자동 설치 스크립트

set -e  # 오류 발생 시 스크립트 중단

echo "🚀 Playwright 기반 크롤링 파이프라인 설치 시작"
echo "=================================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python 버전 확인
echo "📋 Python 버전 확인 중..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo "✅ Python ${PYTHON_VERSION} 발견"

    # Python 3.10+ 확인
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"; then
        echo "✅ Python 버전 요구사항 충족 (3.10+)"
    else
        echo "${RED}❌ Python 3.10 이상이 필요합니다. 현재 버전: ${PYTHON_VERSION}${NC}"
        exit 1
    fi
else
    echo "${RED}❌ Python3이 설치되지 않았습니다.${NC}"
    echo "Python 3.10+ 설치 후 다시 실행해주세요."
    exit 1
fi

# 가상환경 생성
echo "📦 가상환경 생성 중..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 가상환경 생성 완료"
else
    echo "📁 기존 가상환경 발견"
fi

# 가상환경 활성화
echo "🔄 가상환경 활성화 중..."
source venv/bin/activate
echo "✅ 가상환경 활성화 완료"

# pip 업그레이드
echo "⬆️ pip 업그레이드 중..."
pip install --upgrade pip
echo "✅ pip 업그레이드 완료"

# 의존성 패키지 설치
echo "📚 의존성 패키지 설치 중..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ 패키지 설치 완료"
else
    echo "${RED}❌ requirements.txt 파일을 찾을 수 없습니다.${NC}"
    exit 1
fi

# Playwright 브라우저 설치
echo "🎭 Playwright 브라우저 설치 중..."
playwright install chromium
echo "✅ Chromium 브라우저 설치 완료"

# 환경 변수 파일 생성
echo "⚙️ 환경 변수 파일 설정 중..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env 파일 생성 완료 (.env.example에서 복사)"
        echo "${YELLOW}⚠️ .env 파일을 편집하여 데이터베이스 설정을 완료하세요${NC}"
    else
        echo "${RED}❌ .env.example 파일을 찾을 수 없습니다.${NC}"
    fi
else
    echo "📁 기존 .env 파일 발견"
fi

# 로그 디렉토리 생성
echo "📁 로그 디렉토리 생성 중..."
mkdir -p logs
echo "✅ 로그 디렉토리 생성 완료"

# 데이터베이스 연결 테스트 (선택적)
echo "🗄️ 데이터베이스 연결 테스트..."
if python3 -c "
try:
    from models.database import test_connection
    if test_connection():
        print('✅ 데이터베이스 연결 성공')
    else:
        print('⚠️ 데이터베이스 연결 실패 - .env 파일에서 DB 설정을 확인하세요')
except Exception as e:
    print(f'⚠️ 데이터베이스 테스트 건너뛰기: {e}')
" 2>/dev/null; then
    :
else
    echo "${YELLOW}⚠️ 데이터베이스 설정을 나중에 완료하세요${NC}"
fi

# 설치 완료 메시지
echo ""
echo "🎉 설치가 성공적으로 완료되었습니다!"
echo "=================================================="
echo ""
echo "📋 다음 단계:"
echo "1. .env 파일 편집: nano .env"
echo "2. 데이터베이스 설정 완료"
echo "3. 가상환경 활성화: source venv/bin/activate"
echo "4. 예제 실행: python examples/01_playwright_setup.py"
echo ""
echo "📚 도움말:"
echo "- README.md 파일을 참조하세요"
echo "- 문제 발생시 GitHub Issues에 신고하세요"
echo ""
echo "${GREEN}해피 크롤링! 🕷️${NC}"
