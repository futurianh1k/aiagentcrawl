# Multi-stage build for Agent service
FROM python:3.11-slim as builder

# 작업 디렉토리 설정
WORKDIR /build

# 시스템 의존성 설치 (빌드용)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 복사 및 의존성 설치
COPY agent/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# FastAPI 서버 의존성 추가
RUN pip install --no-cache-dir fastapi uvicorn[standard] httpx pydantic

# Playwright 설치 (브라우저는 런타임 이미지에서 설치)
RUN pip install --no-cache-dir playwright>=1.40.0

# 운영 환경 이미지
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 사용자 생성 (보안)
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Chrome 및 ChromeDriver 설치를 위한 시스템 패키지
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Google Chrome 설치 (최신 방식 - apt-key 대신 사용)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 직접 다운로드 및 설치 (Selenium용, ChromeDriverManager 우회)
# Chrome 버전과 호환되는 ChromeDriver 설치
RUN CHROME_VERSION=$(google-chrome --version | sed 's/Google Chrome //g' | cut -d. -f1) \
    && echo "Chrome version: $CHROME_VERSION" \
    && CHROMEDRIVER_VERSION=$(curl -s "https://googlechromelabs.github.io/chrome-for-testing/LATEST_RELEASE_$CHROME_VERSION") \
    && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
    && wget -q "https://storage.googleapis.com/chrome-for-testing-public/$CHROMEDRIVER_VERSION/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip \
    && unzip -q /tmp/chromedriver.zip -d /tmp \
    && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64 \
    && chromedriver --version

# Playwright 브라우저 설치 (전역 경로에 설치하여 모든 사용자가 접근 가능)
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
RUN pip install --no-cache-dir playwright>=1.40.0 \
    && mkdir -p /opt/playwright-browsers \
    && playwright install chromium \
    && playwright install-deps chromium \
    && chmod -R 755 /opt/playwright-browsers

# 빌드 단계에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 공통 모듈 복사
COPY common/ ./common/

# Agent 코드 복사
COPY agent/ ./agent/

# /tmp/.wdm 디렉토리 미리 생성 및 권한 설정 (ChromeDriverManager용)
RUN mkdir -p /tmp/.wdm && chmod 777 /tmp/.wdm

# 앱 사용자로 전환
USER appuser

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99
# FutureWarning 억제 (google.generativeai deprecated 경고)
ENV PYTHONWARNINGS=ignore::FutureWarning:google.generativeai
# ChromeDriverManager 환경 변수 (권한 문제 해결)
ENV WDM_LOCAL=1
ENV WDM_LOG_LEVEL=0
ENV HOME=/tmp
ENV WDM_PATH=/tmp/.wdm
# Playwright 브라우저 경로 (appuser도 접근 가능)
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 포트 노출
EXPOSE 8001

# Agent 서비스 실행
CMD ["python", "-m", "agent.server"]
