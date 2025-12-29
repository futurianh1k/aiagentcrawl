# 에러 확인 가이드

Docker 컨테이너에서 발생하는 에러를 확인하는 다양한 방법을 안내합니다.

## 🚀 빠른 확인 (터미널)

### 1. 실시간 로그 확인

```bash
# Agent 서비스 로그 (실시간)
docker-compose logs -f agent

# 백엔드 로그 (실시간)
docker-compose logs -f backend

# 프론트엔드 로그 (실시간)
docker-compose logs -f frontend

# 모든 서비스 로그 (실시간)
docker-compose logs -f
```

### 2. 최근 에러만 확인

```bash
# 최근 100줄 로그
docker-compose logs --tail=100 agent

# 에러만 필터링 (PowerShell)
docker-compose logs agent | Select-String -Pattern "Error|Exception|Failed|Traceback"

# 에러만 필터링 (Linux/Mac)
docker-compose logs agent | grep -i "error\|exception\|failed\|traceback"
```

### 3. 특정 시간대 로그 확인

```bash
# 최근 10분간 로그
docker-compose logs --since 10m agent

# 특정 시간 이후 로그
docker-compose logs --since 2024-12-29T16:00:00 agent
```

## 🖥️ Portainer를 통한 확인

### 접속 방법
1. 브라우저에서 http://localhost:9000 접속
2. 로그인 (초기 설정 시 생성한 계정)

### 로그 확인 단계
1. **Containers** 메뉴 클릭
2. 확인할 컨테이너 선택:
   - `news-sentiment-backend` - 백엔드 API 서버
   - `news-sentiment-agent` - AI Agent 서비스
   - `news-sentiment-frontend` - 프론트엔드
   - `news-sentiment-mysql` - 데이터베이스
3. **Logs** 탭 클릭
4. 실시간 로그 확인

### Portainer 로그 기능
- ✅ **Auto-refresh**: 자동 새로고침
- ✅ **Search**: 로그 내 검색
- ✅ **Download**: 로그 다운로드
- ✅ **Filter**: 로그 레벨 필터링

## 🔍 일반적인 에러 패턴

### Agent 서비스 에러

```bash
# Agent 서비스 로그 확인
docker-compose logs agent | Select-String -Pattern "Error|Exception"

# 일반적인 에러:
# - "Agent가 초기화되지 않았습니다"
# - "OPENAI_API_KEY가 필요합니다"
# - "WebDriver 초기화 실패"
# - "뉴스 스크레이핑 중 오류"
```

### 백엔드 에러

```bash
# 백엔드 로그 확인
docker-compose logs backend | Select-String -Pattern "Error|Exception|500"

# 일반적인 에러:
# - "Agent 서비스 호출 실패"
# - "데이터베이스 연결 오류"
# - "500 Internal Server Error"
```

### 프론트엔드 에러

```bash
# 프론트엔드 로그 확인
docker-compose logs frontend | Select-String -Pattern "Error|Failed"

# 일반적인 에러:
# - "Build failed"
# - "Module not found"
# - "Port already in use"
```

## 📊 컨테이너 상태 확인

### 전체 상태 확인

```bash
# 모든 컨테이너 상태
docker-compose ps

# 특정 컨테이너 상태
docker-compose ps agent
```

### 헬스체크 확인

```bash
# 컨테이너 헬스 상태
docker ps --format "table {{.Names}}\t{{.Status}}"
```

## 🛠️ 문제 해결 단계

### 1단계: 컨테이너 상태 확인
```bash
docker-compose ps
```
- 모든 컨테이너가 "Up" 상태인지 확인
- "Restarting" 또는 "Exited" 상태면 문제 있음

### 2단계: 최근 로그 확인
```bash
docker-compose logs --tail=50 agent
docker-compose logs --tail=50 backend
```

### 3단계: 에러 패턴 검색
```bash
docker-compose logs agent | Select-String -Pattern "Error|Exception|Traceback"
```

### 4단계: 컨테이너 재시작
```bash
# 문제가 있는 컨테이너만 재시작
docker-compose restart agent

# 전체 재시작
docker-compose restart
```

## 💡 유용한 명령어 모음

```bash
# 실시간 로그 (가장 많이 사용)
docker-compose logs -f agent

# 최근 100줄 + 실시간
docker-compose logs --tail=100 -f agent

# 여러 서비스 동시 확인
docker-compose logs -f agent backend

# 에러만 필터링 (PowerShell)
docker-compose logs agent | Select-String -Pattern "Error|Exception|Failed"

# 로그를 파일로 저장
docker-compose logs agent > agent_logs.txt

# 특정 시간 이후 로그
docker-compose logs --since 30m agent
```

## 🔗 관련 문서

- [Docker 로그 확인 가이드](./DOCKER_LOGS_GUIDE.md)
- [Portainer 설정 가이드](./PORTAINER_SETUP.md)
- [문제 해결 가이드](./troubleshooting.md)

