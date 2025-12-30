#!/bin/bash
# Docker 포트 충돌 해결 스크립트

set -e

echo "🔍 Docker 컨테이너 정리 중..."
docker-compose down

echo "🔍 Docker 시스템 정리 중..."
docker system prune -f

echo "🚀 Docker Compose 서비스 시작 중..."
docker-compose up -d

echo "⏳ 서비스 시작 대기 중 (10초)..."
sleep 10

echo "📊 서비스 상태 확인:"
docker-compose ps

echo ""
echo "✅ 완료! 로그를 확인하려면:"
echo "   docker-compose logs -f"
