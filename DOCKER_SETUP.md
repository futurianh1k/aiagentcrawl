# Docker Compose 설정 가이드

## 🚀 빠른 시작

### 1. 환경 변수 설정

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집하여 API 키 설정
# 특히 OPENAI_API_KEY는 필수입니다
```

### 2. 전체 스택 실행

```bash
# 모든 서비스 시작 (frontend, backend, agent, mysql, redis)
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
- **MySQL**: localhost:3306
- **Redis**: localhost:6379

## 📋 서비스 구성

### 1. MySQL (데이터베이스)
- 포트: 3306
- 데이터베이스: `news_sentiment`
- 자동 초기화: `setup_database/04_database_setup.sql` 실행

### 2. Redis (캐싱)
- 포트: 6379
- 비밀번호: 선택사항 (환경 변수로 설정)

### 3. Agent (Python Agent)
- Agent 서비스는 backend에서 호출됩니다
- 독립 실행이 필요한 경우: `docker-compose --profile agent-standalone up agent`

### 4. Backend (FastAPI)
- 포트: 8000
- Agent, common 모듈을 볼륨으로 마운트
- MySQL, Redis에 의존

### 5. Frontend (Next.js)
- 포트: 3000
- Backend에 의존

### 6. Nginx (선택사항)
- 포트: 80, 443
- 실행: `docker-compose --profile nginx up nginx`

## 🔧 개발 환경 설정

### 볼륨 마운트 활성화

```bash
# docker-compose.override.yml.example을 복사
cp docker-compose.override.yml.example docker-compose.override.yml

# 개발 모드로 실행 (코드 변경 시 자동 반영)
docker-compose up -d
```

## 📝 유용한 명령어

### 서비스 관리

```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d backend frontend

# 서비스 중지
docker-compose stop

# 서비스 중지 및 컨테이너 제거
docker-compose down

# 볼륨까지 제거 (주의: 데이터 삭제됨)
docker-compose down -v
```

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f agent

# 최근 100줄만 보기
docker-compose logs --tail=100 backend
```

### 재빌드

```bash
# 특정 서비스 재빌드
docker-compose build backend

# 캐시 없이 재빌드
docker-compose build --no-cache backend

# 모든 서비스 재빌드
docker-compose build --no-cache
```

### 컨테이너 접속

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# Agent 컨테이너 접속
docker-compose exec agent bash

# MySQL 접속
docker-compose exec mysql mysql -u newsuser -p news_sentiment
```

### 상태 확인

```bash
# 서비스 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats

# 네트워크 확인
docker network ls
docker network inspect aiagent_news-network
```

## 🔒 보안 주의사항

1. **환경 변수**: `.env` 파일은 절대 Git에 커밋하지 마세요
2. **비밀번호**: 프로덕션에서는 강력한 비밀번호 사용
3. **SECRET_KEY**: 프로덕션에서 반드시 변경
4. **API 키**: 로그에 노출되지 않도록 주의

## 🐛 문제 해결

### 포트 충돌

```bash
# 포트 사용 확인
netstat -ano | findstr :3000  # Windows
lsof -i :3000                 # Mac/Linux

# docker-compose.yml에서 포트 변경
```

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs [service_name]

# 컨테이너 재시작
docker-compose restart [service_name]

# 완전히 재생성
docker-compose up -d --force-recreate [service_name]
```

### 데이터베이스 연결 오류

```bash
# MySQL 컨테이너 상태 확인
docker-compose ps mysql

# MySQL 로그 확인
docker-compose logs mysql

# MySQL 재시작
docker-compose restart mysql
```

### Agent 서비스 오류

```bash
# Agent 로그 확인
docker-compose logs agent

# Chrome 설치 확인
docker-compose exec agent google-chrome --version

# Python 경로 확인
docker-compose exec agent python -c "import sys; print(sys.path)"
```

## 📚 추가 자료

- [Docker Compose 공식 문서](https://docs.docker.com/compose/)
- [프로젝트 README](README.md)
- [Agent README](agent/README.md)

