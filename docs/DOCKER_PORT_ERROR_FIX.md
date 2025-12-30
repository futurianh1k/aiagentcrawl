# Docker 포트 충돌 오류 해결 방법

## 문제 증상
```
Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:3306 -> 127.0.0.1:0: /forwards/expose returned unexpected status: 500
```

## 원인
Windows 10 + WSL2 + Docker Desktop 환경에서 포트 포워딩 문제가 발생할 수 있습니다:
1. 포트 3306이 이미 사용 중 (로컬 MySQL 등)
2. 이전 Docker 컨테이너가 아직 실행 중
3. Docker Desktop의 포트 포워딩 설정 문제

## 해결 방법

### 방법 1: 기존 컨테이너 정리 및 재시작 (권장)

```bash
# 모든 컨테이너 중지 및 제거
docker-compose down

# 다시 시작
docker-compose up -d
```

### 방법 2: Windows에서 포트 사용 확인

Windows PowerShell에서:

```powershell
# 포트 3306 사용 확인
netstat -ano | findstr :3306

# 포트를 사용하는 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### 방법 3: MySQL 포트 변경 (적용됨 ✅)

포트 3306 충돌을 해결하기 위해 MySQL 외부 포트를 3307로 변경했습니다:

```yaml
# docker-compose.yml
mysql:
  ports:
    - "3307:3306"  # 외부 포트 3307, 내부 포트 3306 (WSL2 포트 충돌 방지)
```

**중요**: 
- 외부에서 MySQL에 접속하려면 포트 **3307**을 사용하세요
- 컨테이너 간 통신은 여전히 포트 3306을 사용합니다 (내부 포트)
- 백엔드 코드는 변경할 필요 없습니다 (컨테이너 네트워크 내부 통신)

포트 3306이 필요하지 않다면 외부 포트 매핑을 제거할 수도 있습니다:

```yaml
mysql:
  ports:
    # - "3306:3306"  # 이 줄을 주석 처리 (컨테이너 간 통신만 필요할 때)
```

### 방법 4: Docker Desktop 재시작

1. Windows에서 Docker Desktop 완전 종료
2. Docker Desktop 다시 시작
3. WSL2에서 다시 시도

## 빠른 해결 스크립트

```bash
# 1. 모든 컨테이너 중지 및 제거
docker-compose down

# 2. Docker 시스템 정리 (선택사항)
docker system prune -f

# 3. 다시 시작
docker-compose up -d

# 4. 상태 확인
docker-compose ps
```

## 예방 방법

1. **로컬 MySQL 비활성화**: Windows에 설치된 MySQL이 있다면 서비스에서 비활성화
2. **포트 확인**: docker-compose 실행 전 포트 사용 여부 확인
3. **정리된 종료**: 컨테이너 종료 시 `docker-compose down` 사용

## 현재 포트 설정

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **Agent 서비스**: http://localhost:8001
- **MySQL**: localhost:3307 (외부 접속), 내부: 3306
- **Redis**: localhost:6379

## 참고

- 다른 서비스 포트들도 확인: 3000, 6379, 8000, 8001
- 포트 충돌 시 로그: `docker-compose logs mysql`
- MySQL 외부 접속: `mysql -h localhost -P 3307 -u newsuser -p`
