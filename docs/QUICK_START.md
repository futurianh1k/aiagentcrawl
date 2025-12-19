# 🚀 빠른 시작 가이드

## Docker Compose로 전체 스택 실행

### 1. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집 (필수: OPENAI_API_KEY 설정)
# Windows: notepad .env
# Linux/Mac: nano .env
```

`.env` 파일에 최소한 다음을 설정하세요:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 전체 스택 실행

```bash
# 모든 서비스 시작 (mysql, redis, agent, backend, frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f agent
```

### 3. 서비스 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Agent 서비스**: http://localhost:8001
- **Agent 헬스체크**: http://localhost:8001/health

### 4. 서비스 상태 확인

```bash
# 모든 서비스 상태 확인
docker-compose ps

# 특정 서비스 재시작
docker-compose restart backend

# 모든 서비스 중지
docker-compose stop

# 모든 서비스 중지 및 컨테이너 제거
docker-compose down
```

## 📋 서비스 구성

1. **MySQL** (포트 3306): 데이터베이스
2. **Redis** (포트 6379): 캐싱
3. **Agent** (포트 8001): Python Agent 서비스
4. **Backend** (포트 8000): FastAPI 백엔드
5. **Frontend** (포트 3000): Next.js 프론트엔드

## 🔧 문제 해결

### 포트 충돌
```bash
# 포트 사용 확인 (Windows)
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :8001

# 포트 사용 확인 (Linux/Mac)
lsof -i :3000
lsof -i :8000
lsof -i :8001
```

### 서비스 재빌드
```bash
# 특정 서비스 재빌드
docker-compose build --no-cache agent
docker-compose build --no-cache backend
docker-compose build --no-cache frontend

# 모든 서비스 재빌드
docker-compose build --no-cache
```

### 로그 확인
```bash
# Agent 로그
docker-compose logs agent

# Backend 로그
docker-compose logs backend

# Frontend 로그
docker-compose logs frontend
```

## 📚 자세한 문서

- [DOCKER_SETUP.md](DOCKER_SETUP.md): 상세한 Docker 설정 가이드
- [README.md](README.md): 프로젝트 전체 문서

