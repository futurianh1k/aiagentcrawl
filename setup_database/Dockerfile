# Dockerfile for the crawler using the Playwright base image
# - Playwright 이미지에는 Chromium 등의 브라우저 실행에 필요한 시스템 라이브러리들이 이미 포함되어 있어
#   별도의 apt-get으로 브라우저 종속성을 설치할 필요가 없습니다.
# - 이 이미지는 CI/CD 및 컨테이너화된 환경에서 Playwright 테스트/크롤러를 안정적으로 실행하기 좋습니다.

FROM mcr.microsoft.com/playwright:latest

# 작업 디렉터리 설정
WORKDIR /app

# package 파일만 먼저 복사하여 의존성 설치를 캐시(빌드 시간 단축)
COPY package.json package-lock.json* ./
# production 모드로 설치 (개발 의존성은 CI에서 별도 설치 가능)
RUN npm ci --only=production

# 앱 전체 복사
COPY . .

# 크롤러가 결과를 저장할 디렉터리 생성 (호스트와 볼륨으로 연결 가능)
RUN mkdir -p /data

# 환경 변수
ENV NODE_ENV=production

# 기본 실행 커맨드 (docker-compose 또는 실행 시 오버라이드 가능)
CMD ["node", "crawler/naver_shopping_crawler.js"]
