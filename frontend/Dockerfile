# Multi-stage build for Next.js frontend
FROM node:18-alpine as builder

# 작업 디렉토리 설정
WORKDIR /build

# 패키지 파일 복사
COPY package*.json ./

# 의존성 설치 (package-lock.json이 없을 수 있으므로 npm install 사용)
RUN npm install && npm cache clean --force

# 소스 코드 복사
COPY . .

# Next.js 애플리케이션 빌드
RUN npm run build

# 운영 환경 이미지
FROM node:18-alpine

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 사용자 생성 (보안)
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# 필요한 패키지 설치
RUN apk add --no-cache curl

# Next.js standalone 빌드 결과물 복사
COPY --from=builder --chown=nextjs:nodejs /build/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /build/.next/static ./.next/static

# public 폴더 복사 (이제 public 폴더가 존재함)
COPY --from=builder --chown=nextjs:nodejs /build/public ./public

# 앱 사용자로 전환
USER nextjs

# 환경 변수 설정
ENV NODE_ENV=production
ENV HOSTNAME="0.0.0.0"
ENV PORT=3000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# 포트 노출
EXPOSE 3000

# 애플리케이션 실행 (standalone 모드)
CMD ["node", "server.js"]
