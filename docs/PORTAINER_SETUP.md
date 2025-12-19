# Portainer 설정 가이드

## Portainer란?

Portainer는 Docker와 Kubernetes 환경을 웹 UI로 관리할 수 있는 오픈소스 도구입니다.

## 주요 기능

1. **컨테이너 관리**
   - 시작/중지/재시작
   - 로그 실시간 확인
   - 환경 변수 확인 및 수정
   - 컨테이너 내부 쉘 접근

2. **이미지 관리**
   - 이미지 목록 확인
   - 이미지 빌드
   - 이미지 삭제

3. **볼륨 관리**
   - 볼륨 목록 및 사용량 확인
   - 볼륨 생성/삭제

4. **네트워크 관리**
   - 네트워크 목록 확인
   - 네트워크 생성/삭제

5. **모니터링**
   - CPU, 메모리 사용량
   - 네트워크 트래픽
   - 디스크 사용량

## 설치 및 실행

### 1. Portainer 시작

```bash
# Portainer 프로필로 시작
docker-compose --profile portainer up -d portainer

# 또는 docker-compose.yml에서 profiles 제거 후 일반 서비스로 실행
```

### 2. 접속

브라우저에서 접속:
- **HTTP**: http://localhost:9000
- **HTTPS**: https://localhost:9443 (권장)

### 3. 초기 설정

1. 첫 접속 시 관리자 계정 생성
   - Username: `admin` (또는 원하는 이름)
   - Password: 강력한 비밀번호 입력

2. 환경 선택
   - **Docker**: "Docker" 선택
   - **Local**: "Get Started" 클릭

## 사용 방법

### 로그 확인

1. Portainer 접속
2. 왼쪽 메뉴에서 **Containers** 클릭
3. 확인할 컨테이너 선택 (예: `news-sentiment-agent`)
4. **Logs** 탭 클릭
5. 실시간 로그 확인 가능

### 컨테이너 재시작

1. **Containers** 메뉴
2. 컨테이너 선택
3. **Restart** 버튼 클릭

### 환경 변수 확인/수정

1. 컨테이너 선택
2. **Duplicate/Edit** 클릭
3. **Environment variables** 섹션에서 확인/수정
4. **Deploy the container** 클릭

### 리소스 모니터링

1. 컨테이너 선택
2. **Stats** 탭에서 실시간 리소스 사용량 확인

## 보안 주의사항

⚠️ **중요**: Portainer는 Docker 소켓에 접근할 수 있으므로 보안에 주의해야 합니다.

### 프로덕션 환경 권장사항

1. **HTTPS 사용**: 9443 포트 사용 (SSL/TLS)
2. **인증 강화**: 강력한 비밀번호 설정
3. **네트워크 격리**: 내부 네트워크에서만 접근 가능하도록 설정
4. **방화벽 설정**: 외부에서 직접 접근 차단

### 보안 강화 예시

```yaml
portainer:
  image: portainer/portainer-ce:latest
  container_name: news-sentiment-portainer
  restart: unless-stopped
  ports:
    - "127.0.0.1:9000:9000"  # localhost에서만 접근
    - "127.0.0.1:9443:9443"
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - portainer_data:/data
  networks:
    - news-network
  profiles:
    - portainer
```

## Portainer 없이 로그 확인하는 방법

### 빠른 명령어

```bash
# 실시간 로그 (가장 많이 사용)
docker-compose logs -f agent

# 최근 100줄
docker-compose logs --tail=100 agent

# 에러만 필터링 (PowerShell)
docker-compose logs agent | Select-String -Pattern "Error|Exception"

# 여러 서비스 동시 확인
docker-compose logs -f agent backend
```

## 비교: Portainer vs 명령어

| 기능 | Portainer | 명령어 |
|------|-----------|--------|
| 로그 확인 | ✅ 웹 UI, 편리 | ✅ 빠름, 스크립트 가능 |
| 컨테이너 관리 | ✅ 클릭으로 간편 | ⚠️ 명령어 필요 |
| 모니터링 | ✅ 그래프 제공 | ⚠️ 별도 도구 필요 |
| 환경 변수 수정 | ✅ UI로 편리 | ⚠️ 재시작 필요 |
| 학습 곡선 | ✅ 쉬움 | ⚠️ 명령어 학습 필요 |

## 추천

- **개발 환경**: Portainer 사용 권장 (편리함)
- **프로덕션 환경**: 명령어 사용 권장 (보안, 리소스 절약)

