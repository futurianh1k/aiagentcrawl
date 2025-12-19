# Docker 로그 확인 가이드

## 빠른 참조

### 기본 명령어

```bash
# 특정 서비스 로그 확인 (실시간)
docker-compose logs -f agent

# 최근 50줄만 보기
docker-compose logs --tail=50 agent

# 여러 서비스 동시 확인
docker-compose logs -f agent backend

# 타임스탬프 포함
docker-compose logs -ft agent
```

---

## 컨테이너별 로그 확인

### 1. Agent 서비스

```bash
# 실시간 로그 (가장 많이 사용)
docker-compose logs -f agent

# 최근 100줄
docker-compose logs --tail=100 agent

# 에러만 필터링
docker-compose logs agent | Select-String -Pattern "Error|Exception|Traceback"

# 특정 키워드 검색
docker-compose logs agent | Select-String -Pattern "API_KEY|LangChain"
```

### 2. Backend 서비스

```bash
# 실시간 로그
docker-compose logs -f backend

# 최근 50줄
docker-compose logs --tail=50 backend

# API 요청 로그만 보기
docker-compose logs backend | Select-String -Pattern "GET|POST|PUT|DELETE"
```

### 3. Frontend 서비스

```bash
# 실시간 로그
docker-compose logs -f frontend

# 빌드 오류 확인
docker-compose logs frontend | Select-String -Pattern "error|Error|ERROR"
```

### 4. MySQL 서비스

```bash
# 실시간 로그
docker-compose logs -f mysql

# 쿼리 로그 확인 (설정된 경우)
docker-compose logs mysql | Select-String -Pattern "Query"
```

### 5. Redis 서비스

```bash
# 실시간 로그
docker-compose logs -f redis

# 연결 로그 확인
docker-compose logs redis | Select-String -Pattern "connected|connection"
```

### 6. Portainer (선택사항)

```bash
# Portainer 로그
docker-compose logs -f portainer
```

---

## 고급 사용법

### 특정 시간 이후 로그

```bash
# 최근 10분간 로그
docker-compose logs --since 10m agent

# 최근 1시간 로그
docker-compose logs --since 1h agent

# 특정 시간 이후 (예: 2025-12-20T02:00:00)
docker-compose logs --since "2025-12-20T02:00:00" agent
```

### 타임스탬프 포함

```bash
# 타임스탬프 포함 실시간 로그
docker-compose logs -ft agent

# 타임스탬프 포함 최근 50줄
docker-compose logs -t --tail=50 agent
```

### 여러 서비스 동시 모니터링

```bash
# Agent와 Backend 동시 확인
docker-compose logs -f agent backend

# 모든 서비스 동시 확인
docker-compose logs -f

# 특정 서비스 제외
docker-compose logs -f agent backend frontend
```

### PowerShell에서 필터링

```bash
# 에러만 찾기
docker-compose logs agent | Select-String -Pattern "Error|Exception|Traceback" -Context 2,2

# 특정 키워드 검색 (대소문자 구분 없음)
docker-compose logs agent | Select-String -Pattern "api_key" -CaseSensitive:$false

# 여러 패턴 검색
docker-compose logs agent | Select-String -Pattern "Error|Warning|INFO"

# 최근 로그에서 에러 찾기
docker-compose logs --tail=200 agent | Select-String -Pattern "Error"
```

---

## Docker 명령어 직접 사용

### 컨테이너 이름으로 로그 확인

```bash
# 컨테이너 이름으로 로그 확인
docker logs news-sentiment-agent

# 실시간 로그
docker logs -f news-sentiment-agent

# 최근 100줄
docker logs --tail=100 news-sentiment-agent

# 타임스탬프 포함
docker logs -t news-sentiment-agent
```

### 모든 컨테이너 로그 한번에 확인

```bash
# 모든 컨테이너 목록
docker ps --format "table {{.Names}}\t{{.Status}}"

# 각 컨테이너별로 로그 확인
docker logs news-sentiment-agent --tail=20
docker logs news-sentiment-backend --tail=20
docker logs news-sentiment-frontend --tail=20
docker logs news-sentiment-mysql --tail=20
docker logs news-sentiment-redis --tail=20
```

---

## 실용적인 조합 명령어

### 1. 에러 로그만 빠르게 확인

```bash
# Agent 에러만 확인
docker-compose logs --tail=200 agent | Select-String -Pattern "Error|Exception|Traceback|Failed" -Context 1,1

# Backend 에러만 확인
docker-compose logs --tail=200 backend | Select-String -Pattern "Error|Exception|Traceback|Failed" -Context 1,1
```

### 2. 최근 시작 로그 확인

```bash
# Agent 최근 시작 로그
docker-compose logs --since 5m agent

# 모든 서비스 최근 5분 로그
docker-compose logs --since 5m
```

### 3. 헬스체크 로그 확인

```bash
# 헬스체크 관련 로그
docker-compose logs agent | Select-String -Pattern "health|Health|HEALTH"

# 헬스체크 실패 확인
docker-compose logs agent | Select-String -Pattern "unhealthy|failed|error" -Context 1,1
```

### 4. API 요청 로그 확인

```bash
# Backend API 요청 로그
docker-compose logs backend | Select-String -Pattern "GET|POST|PUT|DELETE|PATCH" -Context 0,1

# 특정 엔드포인트만 확인
docker-compose logs backend | Select-String -Pattern "/api/agents"
```

---

## 로그 파일로 저장

### 로그를 파일로 저장

```bash
# Agent 로그를 파일로 저장
docker-compose logs agent > agent_logs.txt

# 타임스탬프 포함하여 저장
docker-compose logs -t agent > agent_logs_with_timestamp.txt

# 여러 서비스 로그 저장
docker-compose logs agent backend > services_logs.txt
```

### 로그 파일에서 검색

```bash
# 저장된 로그 파일에서 검색
Select-String -Path agent_logs.txt -Pattern "Error" -Context 2,2

# 여러 파일에서 검색
Select-String -Path *.txt -Pattern "Error"
```

---

## Portainer를 통한 로그 확인

Portainer를 사용하면 웹 UI에서 로그를 확인할 수 있습니다:

1. **Portainer 접속**: http://localhost:9000
2. **Containers** 메뉴 클릭
3. 확인하고 싶은 컨테이너 클릭
4. **Logs** 탭 클릭
5. 실시간 로그 확인 가능

---

## 문제 해결 시나리오

### 시나리오 1: Agent가 시작되지 않음

```bash
# Agent 로그 전체 확인
docker-compose logs agent

# 최근 에러만 확인
docker-compose logs --tail=50 agent | Select-String -Pattern "Error|Exception|Traceback" -Context 3,3
```

### 시나리오 2: Backend API 오류

```bash
# Backend 최근 로그 확인
docker-compose logs --tail=100 backend

# 500 에러만 확인
docker-compose logs backend | Select-String -Pattern "500|Internal Server Error"
```

### 시나리오 3: 데이터베이스 연결 문제

```bash
# MySQL 로그 확인
docker-compose logs mysql

# Backend의 DB 연결 로그 확인
docker-compose logs backend | Select-String -Pattern "database|mysql|connection"
```

### 시나리오 4: 모든 서비스 상태 확인

```bash
# 모든 서비스 상태 확인
docker-compose ps

# 모든 서비스 최근 로그 확인
docker-compose logs --tail=20
```

---

## 유용한 PowerShell 별칭 (선택사항)

PowerShell 프로필에 다음 별칭을 추가하면 더 편리합니다:

```powershell
# PowerShell 프로필 열기
notepad $PROFILE

# 다음 별칭 추가
function logs-agent { docker-compose logs -f agent }
function logs-backend { docker-compose logs -f backend }
function logs-frontend { docker-compose logs -f frontend }
function logs-all { docker-compose logs -f }
function logs-errors { param($service) docker-compose logs --tail=200 $service | Select-String -Pattern "Error|Exception|Traceback" -Context 2,2 }
```

사용 예:
```bash
logs-agent          # Agent 실시간 로그
logs-backend        # Backend 실시간 로그
logs-errors agent   # Agent 에러만 확인
```

---

## 참고사항

1. **로그 크기 제한**: Docker는 기본적으로 로그 크기를 제한합니다. 필요시 `docker-compose.yml`에서 로그 설정을 조정할 수 있습니다.

2. **로그 로테이션**: 오래된 로그는 자동으로 삭제됩니다. 중요한 로그는 파일로 저장하세요.

3. **성능**: 실시간 로그(`-f`)는 성능에 영향을 줄 수 있으므로, 필요할 때만 사용하세요.

4. **보안**: 로그에 민감한 정보(API 키, 비밀번호 등)가 포함될 수 있으므로 주의하세요.
