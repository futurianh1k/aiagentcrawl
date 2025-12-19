# .env 파일 변경 후 컨테이너 업데이트 가이드

## 방법 1: 특정 서비스만 재시작 (권장)

API 키를 사용하는 서비스만 재시작하면 됩니다:

```bash
# Agent 서비스만 재시작
docker-compose restart agent

# Backend 서비스만 재시작
docker-compose restart backend

# Agent와 Backend 모두 재시작
docker-compose restart agent backend
```

## 방법 2: 전체 서비스 재시작

모든 서비스를 재시작하려면:

```bash
docker-compose restart
```

## 방법 3: 컨테이너 재생성 (환경 변수 변경이 확실히 반영되지 않을 때)

컨테이너를 완전히 재생성하려면:

```bash
# 특정 서비스 재생성
docker-compose up -d --force-recreate agent backend

# 전체 재생성
docker-compose up -d --force-recreate
```

## 방법 4: 환경 변수 직접 확인

컨테이너 내부의 환경 변수를 확인하려면:

```bash
# Agent 컨테이너의 환경 변수 확인
docker-compose exec agent env | grep API_KEY

# Backend 컨테이너의 환경 변수 확인
docker-compose exec backend env | grep API_KEY
```

## 주의사항

1. **MySQL과 Redis는 재시작할 필요 없음**: 이들은 API 키를 사용하지 않습니다.
2. **Frontend는 재시작할 필요 없음**: Frontend는 빌드 시점에 환경 변수가 포함되므로, 변경하려면 재빌드가 필요합니다.
3. **.env 파일 위치**: `.env` 파일은 프로젝트 루트(`docker-compose.yml`과 같은 위치)에 있어야 합니다.

## 빠른 명령어

```bash
# API 키 변경 후 가장 빠른 방법
docker-compose restart agent backend

# 상태 확인
docker-compose ps

# 로그 확인 (문제가 있을 경우)
docker-compose logs agent backend
```

