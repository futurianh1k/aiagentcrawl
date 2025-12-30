# Docker WSL2 연결 오류 해결 방법

## 문제 증상
```
request returned Internal Server Error for API route and version http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/json
```

## 원인
Windows 10에서 WSL2를 사용할 때 Docker Desktop이 제대로 실행되지 않거나 WSL2 통합이 활성화되지 않은 경우 발생합니다.

## 해결 방법

### 방법 1: Docker Desktop 설정 확인 및 재시작 (권장)

1. **Docker Desktop 실행 확인**
   - Windows에서 Docker Desktop이 실행 중인지 확인
   - 시스템 트레이에 Docker 아이콘이 초록색인지 확인

2. **Docker Desktop WSL2 통합 설정**
   - Docker Desktop 열기
   - Settings (⚙️) → Resources → WSL Integration
   - "Enable integration with my default WSL distro" 체크
   - 사용 중인 WSL 배포판 (예: Ubuntu) 옆 토글을 ON
   - "Apply & Restart" 클릭

3. **WSL2에서 확인**
   ```bash
   docker ps
   docker-compose up -d
   ```

### 방법 2: Docker Desktop 재시작

1. Windows에서 Docker Desktop 완전 종료
2. Docker Desktop 다시 시작
3. WSL2 터미널에서 테스트:
   ```bash
   docker ps
   ```

### 방법 3: WSL2 재부팅

```bash
# WSL2 재부팅 (PowerShell에서 실행)
wsl --shutdown

# 또는 Windows에서 WSL2 재시작 후 다시 접속
```

### 방법 4: Docker 서비스 확인 (Linux 내부 Docker 사용 시)

WSL2 내부에서 Docker를 직접 설치한 경우:

```bash
# Docker 서비스 상태 확인
sudo service docker status

# Docker 서비스 시작
sudo service docker start

# 부팅 시 자동 시작 설정
sudo systemctl enable docker  # (WSL2에서는 systemd가 기본적으로 비활성화됨)
```

## 권장 설정: Docker Desktop 사용

Windows 10 + WSL2 환경에서는 **Docker Desktop을 사용하는 것이 권장**됩니다:
- 자동 WSL2 통합
- GUI 관리 도구
- 자동 업데이트
- 리소스 관리 용이

## 확인 명령어

```bash
# Docker 버전 확인
docker --version

# Docker 컨텍스트 확인
docker context ls

# Docker 데몬 연결 확인
docker ps

# Docker 정보 확인
docker info
```

## 추가 문제 해결

### 문제: 여전히 연결 오류가 발생하는 경우

1. **Docker Desktop 완전 재설치**
   - Docker Desktop 완전 제거
   - Windows 재부팅
   - Docker Desktop 재설치

2. **WSL2 배포판 재설정** (최후의 수단)
   ```bash
   # Windows PowerShell에서
   wsl --unregister Ubuntu
   wsl --install -d Ubuntu
   ```

### 문제: 권한 오류가 발생하는 경우

```bash
# docker 그룹에 사용자 추가
sudo usermod -aG docker $USER

# 로그아웃 후 다시 로그인 (또는)
newgrp docker
```

## 참고

- Docker Desktop WSL2 백엔드 문서: https://docs.docker.com/desktop/wsl/
- WSL2 Docker 통합 가이드: https://docs.docker.com/desktop/wsl/troubleshoot/
