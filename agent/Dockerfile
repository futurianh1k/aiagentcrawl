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

# Google Chrome 설치
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 빌드 단계에서 설치된 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 공통 모듈 복사
COPY common/ ./common/

# Agent 코드 복사
COPY agent/ ./agent/

# 앱 사용자로 전환
USER appuser

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 포트 노출
EXPOSE 8001

# Agent 서비스 실행
CMD ["python", "-m", "agent.server"]
