# AI Agent 기반 뉴스 감정 분석 시스템 - 완전 가이드

> **프로젝트 전체 문서 통합본**  
> 작성일: 2025년 12월  
> 버전: 2.0

---

## 📑 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [빠른 시작](#2-빠른-시작)
3. [시스템 아키텍처](#3-시스템-아키텍처)
4. [설치 및 설정](#4-설치-및-설정)
5. [Docker 가이드](#5-docker-가이드)
6. [데이터베이스 가이드](#6-데이터베이스-가이드)
7. [Agent 시스템](#7-agent-시스템)
8. [개발 내역](#8-개발-내역)
9. [문제 해결](#9-문제-해결)
10. [참고 자료](#10-참고-자료)

---

## 1. 프로젝트 개요

### 1.1 프로젝트 소개

**프로젝트명**: AI Agent 기반 뉴스 감정 분석 시스템  
**목적**: LangChain AI Agent를 활용한 실시간 뉴스 감정 분석 시스템  
**기술 스택**: FastAPI, Next.js, LangChain, OpenAI, MySQL, Redis, Docker

### 1.2 주요 기능

- **🤖 AI Agent 기반 분석**: LangChain ReAct 패턴으로 구현된 멀티 에이전트 시스템
- **📊 실시간 감정 분석**: OpenAI API를 활용한 뉴스 기사 및 댓글 감정 분석
- **🔍 지능형 뉴스 수집**: 네이버 뉴스와 구글 뉴스 크롤링 지원
- **📈 데이터 시각화**: Recharts를 활용한 감정 분포 및 키워드 클라우드
- **🚀 확장 가능한 아키텍처**: 마이크로서비스 아키텍처 및 컨테이너화
- **⚡ 고성능 처리**: 비동기 처리 및 Redis 캐싱

### 1.3 기술 스택

#### Backend
- **FastAPI** 0.104.1 - 비동기 웹 프레임워크
- **LangChain** 0.0.335 - AI Agent 프레임워크
- **SQLAlchemy** 2.0.23 - ORM 및 데이터베이스 관리
- **MySQL** 8.0 - 주 데이터베이스
- **Redis** 7.2 - 캐싱 및 세션 관리
- **OpenAI API** - 감정 분석 및 자연어 처리

#### Frontend
- **Next.js** 14.0.3 - React 기반 풀스택 프레임워크
- **TypeScript** 5.2.2 - 타입 안정성
- **Tailwind CSS** 3.3.6 - 유틸리티 우선 CSS 프레임워크
- **Recharts** 2.8.0 - 데이터 시각화
- **Axios** 1.6.2 - HTTP 클라이언트

#### Agent
- **Python 3.11** - Agent 실행 환경
- **Playwright** - 웹 크롤링 (네이버/구글 뉴스)
- **Selenium** - 웹 크롤링 (폴백)
- **LangChain** - AI Agent 프레임워크
- **OpenAI/Gemini** - 감성 분석

#### DevOps
- **Docker** & **Docker Compose** - 컨테이너화
- **GitHub Actions** - CI/CD 파이프라인
- **Nginx** - 리버스 프록시 (선택사항)

### 1.4 프로젝트 구조

```
aiagent/
├── agent/                      # Python Agent
│   ├── news_agent.py          # News Analysis Agent
│   ├── server.py              # Agent HTTP 서버
│   ├── tools/                 # Agent Tools
│   │   ├── news_scraper/     # 뉴스 크롤링 Tool (네이버/구글)
│   │   └── data_analyzer/    # 감성 분석 Tool
│   └── Dockerfile
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── main.py           # FastAPI 엔트리포인트
│   │   ├── api/routes/       # API 라우터
│   │   ├── services/         # 비즈니스 로직
│   │   └── core/            # 설정 및 DB
│   └── Dockerfile
├── frontend/                   # Next.js 프론트엔드
│   ├── app/                  # Next.js App Router
│   ├── components/           # React 컴포넌트
│   └── Dockerfile
├── common/                     # 공통 모듈
│   ├── config.py            # 설정 관리
│   ├── models.py            # 공통 데이터 모델
│   ├── utils.py             # 유틸리티 함수
│   └── security.py          # 보안 관련 함수
├── setup_database/            # 데이터베이스 설정
│   ├── 04_database_setup.sql
│   ├── README.md
│   └── troubleshooting.md
├── docs/                      # 문서
│   ├── README.md
│   ├── QUICK_START.md
│   ├── DOCKER_SETUP.md
│   └── ...
├── History/                   # 개발 이력
│   └── 2025-12-29_*.md
├── docker-compose.yml         # 전체 스택 오케스트레이션
├── .env.example              # 환경 변수 템플릿
└── README.md                 # 프로젝트 README
```

---

## 2. 빠른 시작

### 2.1 필수 요구사항

- Docker & Docker Compose
- Node.js 18+ (로컬 개발시)
- Python 3.11+ (로컬 개발시)
- OpenAI API 키

### 2.2 프로젝트 클론 및 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd aiagentcrawl

# 환경 변수 설정
cp .env.example .env
```

### 2.3 환경 변수 구성

`.env` 파일을 편집하여 필요한 값들을 설정하세요:

```bash
# 중요: OpenAI API 키 설정 필수
OPENAI_API_KEY=sk-your-openai-api-key-here

# 데이터베이스 비밀번호 변경 권장
MYSQL_ROOT_PASSWORD=your-secure-password
MYSQL_PASSWORD=your-secure-password

# 프로덕션에서 SECRET_KEY 변경 필수
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 2.4 Docker Compose로 전체 스택 실행

```bash
# 전체 스택 시작 (MySQL, Redis, Agent, Backend, Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

### 2.5 애플리케이션 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Agent 서비스**: http://localhost:8001

---

## 3. 시스템 아키텍처

### 3.1 AI Agent 시스템 아키텍처

#### Agent 구성요소

1. **NewsScrapingAgent**: 뉴스 기사 수집
   - 네이버 뉴스 크롤링
   - 구글 뉴스 크롤링
   - 소스 선택 기능

2. **SentimentAnalysisAgent**: 감정 분석
   - OpenAI GPT 모델 활용
   - 긍정/부정/중립 분류
   - 신뢰도 점수 제공

3. **KeywordExtractionAgent**: 키워드 추출
   - 주요 키워드 식별
   - 빈도수 분석
   - 연관 키워드 매칭

#### ReAct 패턴 구현

```python
# Agent 실행 플로우 예시
async def analyze_news(keyword: str, sources: List[str]):
    # 1. Reasoning: 분석 계획 수립
    plan = await agent.reason(f"Analyze news about '{keyword}' from {sources}")

    # 2. Action: 뉴스 수집
    articles = await news_agent.scrape(keyword, sources)

    # 3. Observation: 결과 관찰
    results = await sentiment_agent.analyze(articles)

    # 4. 최종 응답 생성
    return await agent.synthesize(results)
```

### 3.2 크롤링 시스템 진화

#### Phase 1: Selenium 기반 순차 크롤링 (초기)

```
사용자 요청 → 네이버 크롤링 → 완료 → 구글 크롤링 → 완료 → 감정 분석
                  ↓                      ↓
              약 2분 소요             약 2분 소요
                              
총 소요시간: 4-5분 이상
```

**문제점**:
- 순차 처리로 인한 긴 대기 시간
- 5분 타임아웃 초과 빈번
- ChromeDriver 설치/관리 복잡
- Docker 환경에서 권한 문제 발생

#### Phase 2: Playwright + 병렬처리 (현재)

```
사용자 요청 → ┬─ 네이버 크롤링 ─┬→ 병렬 기사 추출 → 감정 분석
             └─ 구글 크롤링 ──┘
                 (동시 실행)
                              
총 소요시간: 1-2분
```

**개선 효과**:
- 2-3배 속도 향상
- 안정적인 브라우저 자동화
- 네이티브 비동기 지원
- 더 적은 리소스 사용

### 3.3 성능 지표

| 기능 | 이전 성능 | 최적화 후 | 개선율 |
|-----|----------|-----------|--------|
| Batch Insert | 30초 (1000건) | 2초 (1000건) | **15배 향상** |
| 비동기 크롤링 | 50초 (10 URL) | 8초 (10 URL) | **6배 향상** |
| Playwright 병렬 | ~100초 | ~25초 | **4배 향상** |
| Retry 전략 | 즉시 실패 | 지수 백오프 | **안정성 95% 향상** |

---

## 4. 설치 및 설정

### 4.1 로컬 개발 환경 설정

#### Backend 로컬 개발

```bash
cd backend

# Python 가상환경 설정
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
# (Docker Compose MySQL 실행 상태에서)
python -m alembic upgrade head

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend 로컬 개발

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 프로덕션 실행
npm start
```

#### Agent 로컬 개발

```bash
# Agent 테스트
python -m agent.news_agent

# Agent 서버 실행
python -m agent.server
```

### 4.2 환경 변수 업데이트

`.env` 파일 변경 후 컨테이너 업데이트:

```bash
# Agent 서비스만 재시작
docker-compose restart agent

# Backend 서비스만 재시작
docker-compose restart backend

# Agent와 Backend 모두 재시작
docker-compose restart agent backend

# 환경 변수 직접 확인
docker-compose exec agent env | grep API_KEY
docker-compose exec backend env | grep API_KEY
```

**주의사항**:
1. MySQL과 Redis는 재시작할 필요 없음 (API 키를 사용하지 않음)
2. Frontend는 재시작할 필요 없음 (빌드 시점에 환경 변수 포함)
3. `.env` 파일은 프로젝트 루트에 있어야 함

---

## 5. Docker 가이드

### 5.1 Docker Compose 설정

#### 서비스 구성

1. **MySQL** (포트 3307): 데이터베이스
   - 외부 포트: 3307 (WSL2 포트 충돌 방지)
   - 내부 포트: 3306
   - 데이터베이스: `news_sentiment`
   - 자동 초기화: `setup_database/04_database_setup.sql` 실행

2. **Redis** (포트 6379): 캐싱
   - 비밀번호: 선택사항 (환경 변수로 설정)

3. **Agent** (포트 8001): Python Agent 서비스
   - Agent 서비스는 backend에서 호출됨
   - 독립 실행: `docker-compose --profile agent-standalone up agent`

4. **Backend** (포트 8000): FastAPI
   - Agent, common 모듈을 볼륨으로 마운트
   - MySQL, Redis에 의존

5. **Frontend** (포트 3000): Next.js
   - Backend에 의존

6. **Portainer** (포트 9000): Docker 관리 도구 (선택사항)
   - 실행: `docker-compose --profile portainer up portainer`

### 5.2 유용한 명령어

#### 서비스 관리

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

#### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f agent

# 최근 100줄만 보기
docker-compose logs --tail=100 backend

# 에러만 필터링 (PowerShell)
docker-compose logs agent | Select-String -Pattern "Error|Exception|Traceback"

# 에러만 필터링 (Linux/Mac)
docker-compose logs agent | grep -i "error\|exception\|failed\|traceback"
```

#### 재빌드

```bash
# 특정 서비스 재빌드
docker-compose build backend

# 캐시 없이 재빌드
docker-compose build --no-cache backend

# 모든 서비스 재빌드
docker-compose build --no-cache
```

#### 컨테이너 접속

```bash
# Backend 컨테이너 접속
docker-compose exec backend bash

# Agent 컨테이너 접속
docker-compose exec agent bash

# MySQL 접속
docker-compose exec mysql mysql -u newsuser -p news_sentiment
```

### 5.3 Docker 문제 해결

#### 포트 충돌 오류

**증상**:
```
Error response from daemon: ports are not available: exposing port TCP 0.0.0.0:3306
```

**해결 방법**:

1. **기존 컨테이너 정리 및 재시작** (권장)
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Windows에서 포트 사용 확인**
   ```powershell
   netstat -ano | findstr :3306
   taskkill /PID <PID> /F
   ```

3. **MySQL 포트 변경** (적용됨 ✅)
   - 외부 포트를 3307로 변경하여 충돌 방지
   - 외부 접속: `localhost:3307`
   - 컨테이너 간 통신: 여전히 3306 사용

#### WSL2 연결 오류

**증상**:
```
request returned Internal Server Error for API route and version http://%2Fvar%2Frun%2Fdocker.sock/v1.24/containers/json
```

**해결 방법**:

1. **Docker Desktop 설정 확인**
   - Docker Desktop 실행 확인
   - Settings → Resources → WSL Integration
   - "Enable integration with my default WSL distro" 체크
   - 사용 중인 WSL 배포판 옆 토글을 ON
   - "Apply & Restart" 클릭

2. **Docker Desktop 재시작**
   - Windows에서 Docker Desktop 완전 종료
   - Docker Desktop 다시 시작
   - WSL2 터미널에서 테스트: `docker ps`

3. **WSL2 재부팅**
   ```powershell
   wsl --shutdown
   ```

### 5.4 Portainer 설정

Portainer는 Docker와 Kubernetes 환경을 웹 UI로 관리할 수 있는 도구입니다.

#### 설치 및 실행

```bash
# Portainer 프로필로 시작
docker-compose --profile portainer up -d portainer

# 접속
# HTTP: http://localhost:9000
# HTTPS: https://localhost:9443 (권장)
```

#### 주요 기능

1. **컨테이너 관리**
   - 시작/중지/재시작
   - 로그 실시간 확인
   - 환경 변수 확인 및 수정
   - 컨테이너 내부 쉘 접근

2. **로그 확인**
   - Portainer 접속 → Containers 메뉴
   - 확인할 컨테이너 선택
   - Logs 탭 클릭
   - 실시간 로그 확인 가능

3. **리소스 모니터링**
   - CPU, 메모리 사용량
   - 네트워크 트래픽
   - 디스크 사용량

---

## 6. 데이터베이스 가이드

### 6.1 데이터베이스 구조

#### news_sentiment 데이터베이스

| 테이블명 | 설명 | 주요 필드 |
|----------|------|-----------|
| **analysis_sessions** | 분석 세션 정보 | id, keyword, sources, status, created_at |
| **articles** | 크롤링된 기사 | url, title, content, source, published_at, sentiment_label |
| **comments** | 기사 댓글 | text, author, sentiment_label, sentiment_score, confidence |
| **keywords** | 추출된 키워드 | keyword, frequency, sentiment_score |

### 6.2 데이터베이스 접속

#### MySQL 컨테이너 접속

```bash
# 일반 사용자로 접속
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment

# Root 사용자로 접속
docker-compose exec mysql mysql -u root -prootpassword123 news_sentiment
```

#### 기본 쿼리

```sql
-- 분석 세션 목록 확인
SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT 10;

-- 특정 세션의 기사 확인
SELECT * FROM articles WHERE session_id = 1;

-- 댓글 확인
SELECT * FROM comments WHERE article_id = 1;

-- 감정 분포
SELECT sentiment_label, COUNT(*) as count
FROM articles
GROUP BY sentiment_label;
```

### 6.3 데이터베이스 초기화

#### Windows 설정

1. MySQL Installer 다운로드 및 설치
   - [MySQL 공식 다운로드 페이지](https://dev.mysql.com/downloads/installer/)
   - `mysql-installer-community-8.0.xx.x.msi` 다운로드
   - 관리자 권한으로 실행
   - Developer Default 선택

2. MySQL Server 구성
   - Standalone MySQL Server 선택
   - Port: 3306
   - Root 비밀번호 설정
   - Windows Service로 등록

3. 환경 변수 설정
   - 시작 메뉴 → 시스템 환경 변수 편집
   - Path에 `C:\Program Files\MySQL\MySQL Server 8.0\bin` 추가

4. 데이터베이스 초기화
   ```bash
   setup_database.bat
   ```

#### Mac 설정

1. Homebrew 설치 확인
   ```bash
   brew --version
   ```

2. MySQL 설치
   ```bash
   brew install mysql
   brew services start mysql
   ```

3. 보안 설정
   ```bash
   mysql_secure_installation
   ```

4. 데이터베이스 초기화
   ```bash
   chmod +x setup_database.sh
   ./setup_database.sh
   ```

#### Ubuntu 설정

1. 시스템 업데이트
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. MySQL 설치
   ```bash
   sudo apt install -y mysql-server
   sudo systemctl start mysql
   sudo systemctl enable mysql
   ```

3. 보안 설정
   ```bash
   sudo mysql_secure_installation
   ```

4. Root 인증 방식 변경
   ```sql
   sudo mysql
   ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. 데이터베이스 초기화
   ```bash
   chmod +x setup_database.sh
   ./setup_database.sh
   ```

### 6.4 데이터베이스 확인 가이드

#### 방법 1: MySQL 컨테이너 직접 접속

```bash
# MySQL 컨테이너 접속
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment

# 데이터베이스 및 테이블 확인
SHOW DATABASES;
USE news_sentiment;
SHOW TABLES;
DESCRIBE analysis_sessions;
```

#### 방법 2: Docker 명령어로 직접 쿼리 실행

```bash
# 분석 세션 목록 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT 5;"

# 기사 수 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT COUNT(*) as total_articles FROM articles;"
```

#### 방법 3: Backend API를 통한 확인

```bash
# 분석 상태 조회
curl http://localhost:8000/api/agents/status/1
```

### 6.5 데이터베이스 문제 해결

#### 연결 오류

**증상**: `ERROR 2003 (HY000): Can't connect to MySQL server`

**해결**:
```bash
# MySQL 서비스 상태 확인
docker-compose ps mysql

# MySQL 로그 확인
docker-compose logs mysql

# MySQL 재시작
docker-compose restart mysql
```

#### 인증 실패

**증상**: `ERROR 1045 (28000): Access denied`

**해결**:
- 비밀번호 확인
- 환경 변수의 데이터베이스 정보 확인
- Root 비밀번호 재설정 (필요시)

#### 테이블이 없는 경우

```bash
# 데이터베이스 초기화 스크립트 확인
cat setup_database/04_database_setup.sql

# 수동으로 테이블 생성
docker-compose exec mysql mysql -u root -prootpassword123 news_sentiment < setup_database/04_database_setup.sql
```

---

## 7. Agent 시스템

### 7.1 Agent 구조

```
agent/
├── __init__.py              # 패키지 초기화 및 export
├── agent.py                 # Calculator Agent (예제)
├── news_agent.py            # News Analysis Agent (메인)
├── planner_agent.py          # Planner Agent (레거시)
├── tools/                   # Agent Tools
│   ├── __init__.py
│   ├── news_scraper/       # 뉴스 크롤링 Tool
│   │   ├── scraper.py      # 네이버/구글 크롤러
│   │   ├── models.py       # NewsArticle 모델
│   │   └── README.md
│   └── data_analyzer/      # 감성 분석 Tool
│       ├── analyzer.py     # OpenAI/Gemini 감성 분석
│       └── models.py       # SentimentResult 모델
└── node_agent/             # Node.js 버전 (별도)
```

### 7.2 NewsAnalysisAgent 사용

```python
from agent import NewsAnalysisAgent
from common.config import get_config
import asyncio

# Agent 초기화
config = get_config()
agent = NewsAnalysisAgent(config.get_openai_key())

# 비동기 뉴스 분석
async def analyze():
    result = await agent.analyze_news_async(
        keyword="인공지능",
        sources=["네이버", "구글"],
        max_articles=10
    )
    print(f"총 기사 수: {result['total_articles']}")
    print(f"감성 분포: {result['sentiment_distribution']}")

asyncio.run(analyze())

# 자연어 질의
response = agent.analyze_news_sentiment("AI 기술에 대한 최근 뉴스의 여론을 분석해줘")
print(response)
```

### 7.3 크롤링 시스템 상세

#### Playwright vs Selenium 비교

| 항목 | Selenium | Playwright |
|------|----------|------------|
| **속도** | 느림 | 2-3배 빠름 |
| **비동기** | 제한적 (threading) | 네이티브 async/await |
| **자동 대기** | 수동 (explicit wait) | 자동 (auto-waiting) |
| **메모리** | 높음 | 낮음 |
| **브라우저 설치** | WebDriver 별도 관리 | `playwright install` 통합 |
| **병렬처리** | 복잡 | 간단 (asyncio.gather) |

#### 병렬 검색 구현

```python
async def search_news_parallel(self, keyword, sources, max_articles=5):
    tasks = []
    
    if "네이버" in sources:
        tasks.append(("네이버", self.naver_scraper.search_news(keyword, max_articles)))
    if "구글" in sources:
        tasks.append(("구글", self.google_scraper.search_news(keyword, max_articles)))
    
    # 병렬 실행
    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
    
    return {"네이버": results[0], "구글": results[1]}
```

#### 병렬 기사 추출 (Semaphore로 동시 처리 제한)

```python
async def extract_articles_parallel(self, url_map, max_concurrent=5):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def extract_with_limit(url, scraper):
        async with semaphore:  # 최대 5개 동시 처리
            return await scraper.extract_article(url)
    
    tasks = [extract_with_limit(url, scraper) for url, scraper in url_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return [r for r in results if r and not isinstance(r, Exception)]
```

### 7.4 크롤링 최적화

#### 구글 뉴스 RSS 피드 활용

구글 뉴스는 HTML 구조가 복잡하고 자주 변경되므로, **RSS 피드**를 사용하여 안정적으로 URL을 수집합니다.

```python
# RSS 피드 URL
rss_url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"

# XML 파싱으로 링크 추출
response = requests.get(rss_url)
root = ET.fromstring(response.content)
for item in root.findall('.//item/link'):
    urls.append(item.text)
```

#### 불필요한 리소스 차단 (속도 향상)

```python
# 이미지, 폰트 로딩 차단
await context.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico}", lambda route: route.abort())
await context.route("**/*.woff*", lambda route: route.abort())
```

### 7.5 URL 필터링 강화

네이버 뉴스 URL 필터링을 엄격하게 하여 실제 기사만 수집:

```python
# 실제 기사 URL 패턴만 허용
if "n.news.naver.com/mnews/article/" in href:
    # 모바일 뉴스: https://n.news.naver.com/mnews/article/001/0015819227
    is_news_article = True
elif "news.naver.com/main/read" in href:
    # PC 뉴스: https://news.naver.com/main/read.nhn?mode=...
    is_news_article = True
elif "/article/" in href and "news.naver.com" in href:
    # 기타 기사 패턴
    is_news_article = True
```

**제외되는 URL**:
- `https://news.naver.com/` (홈페이지)
- `https://news.naver.com/main/static/...` (정적 페이지)
- `https://news.naver.com/main/list.naver` (목록 페이지)

### 7.6 셀렉터 다중화

네이버 페이지 구조 변경에 대응하기 위해 다중 셀렉터 전략 사용:

```python
# 제목 추출 셀렉터 (7개)
title_selectors = [
    "#ct > div.media_end_head...",  # 기본 셀렉터
    "h2.media_end_head_headline",   # 네이버 뉴스 헤드라인
    "h3.tit_view",                   # 구버전
    ".article_header h2",            # 일반적인 패턴
    "h1", "h2"                       # 기본 태그
]

# 본문 추출 셀렉터 (8개)
content_selectors = [
    "#dic_area",                     # 기본
    "#articeBody",                   # 구버전
    ".article_body",                 # 일반적인 클래스명
    "article",                       # HTML5 표준
    ".news_end_body_container",      # 네이버 특정 구조
    "#newsct_article",               # 네이버 뉴스 컨테이너
]
```

---

## 8. 개발 내역

### 8.1 프로젝트 리팩토링

#### 구조 개선

**변경 전**:
- lab1~lab4 파일들이 모두 `lab1_basic_agent` 폴더에 있음
- 중복 파일들 (`working`, `fixedbychatgpt` 등)이 많음
- 공통 모듈이 분리되지 않음

**변경 후**:
```
aiagent/
├── common/                     # 공통 모듈
│   ├── config.py              # 설정 관리
│   ├── models.py              # 공통 데이터 모델
│   ├── utils.py               # 유틸리티 함수
│   └── security.py            # 보안 관련 함수
├── agent/                      # Agent 패키지
│   ├── news_agent.py          # News Analysis Agent
│   └── tools/                 # Agent Tools
└── ...
```

#### 공통 모듈 추출

1. **common/config.py**: 환경 변수 중앙 관리
2. **common/models.py**: 공통 데이터 모델 정의
3. **common/utils.py**: 안전한 로깅 함수, 입력 검증
4. **common/security.py**: 민감한 데이터 마스킹, API 키 검증

### 8.2 Agent & Tools 리팩토링

#### 주요 개선 사항

1. **네이버/구글 뉴스 선택 기능**
   - 이전: 네이버만 지원
   - 개선: 네이버와 구글 선택 가능

2. **실제 Tools 사용**
   - 이전: 더미 데이터 사용
   - 개선: 실제 Tools 사용 (실제 크롤링, 실제 감성 분석)

3. **비동기 처리**
   - 이전: 동기 처리만 지원
   - 개선: 비동기 처리 지원 (`analyze_news_async()`)

4. **에러 처리 강화**
   - 입력 검증
   - 안전한 로깅 (API 키 노출 방지)
   - 예외 처리 및 기본값 반환

### 8.3 크롤링 시스템 개선 이력

#### 2025-12-29: 네이버 스크래핑 오류 수정

**문제**:
- 네이버 뉴스 검색 시 "기사를 찾을 수 없습니다" 오류
- CSS 셀렉터 실패

**해결**:
1. CSS 셀렉터 다중화 (10개 셀렉터 시도)
2. 셀렉터 우선순위 조정 (구체적 → 포괄적)
3. URL 패턴 매칭 강화 (`/read.nhn`, `/read.naver` 추가)
4. 디버깅 로그 대폭 강화

#### 2025-12-29: 본문 추출 오류 수정

**문제**:
- "no such element: article" 에러
- 네이버 뉴스는 `<article>` 태그 미사용

**해결**:
1. 제목 추출 셀렉터 다중화 (7개)
2. 본문 추출 셀렉터 다중화 (8개)
3. 본문 최소 길이 검증 (50자 이상)
4. 각 셀렉터 시도 과정 상세 로그

#### 2025-12-29: URL 필터링 강화

**문제**:
- 5분 타임아웃 에러
- 홈페이지/채널 페이지도 수집하여 본문 추출 실패

**해결**:
1. URL 필터링 엄격화
   - `/mnews/article/` 패턴만 허용 (모바일)
   - `/main/read` 패턴 허용 (PC)
   - 홈페이지, 채널 페이지 제외
2. 디버깅 정보 강화
   - 본문 추출 실패 시 페이지 정보 출력
   - 스크린샷 자동 저장

### 8.4 보안 개선

#### 적용된 보안 가이드라인

1. **API 키 관리**
   - 환경 변수에서만 읽기
   - 로그에 절대 노출하지 않음 (`safe_log` 사용)
   - `.env.example` 제공

2. **입력 검증**
   - 모든 사용자 입력 검증 (`validate_input`)
   - SQL Injection 방지
   - XSS 방지 (`sanitize_text`)

3. **크롤링 보안**
   - User-Agent 설정
   - robots.txt 준수
   - Rate Limit 준수

4. **에러 처리**
   - 민감한 정보를 에러 메시지에 포함하지 않음
   - 일반화된 에러 메시지 제공

---

## 9. 문제 해결

### 9.1 일반적인 문제들

#### OpenAI API 키 오류

**증상**: API 호출 실패

**해결**:
```bash
# .env 파일의 OPENAI_API_KEY 확인
cat .env | grep OPENAI_API_KEY

# API 키 유효성 및 크레딧 잔액 확인
# https://platform.openai.com/api-keys 에서 확인
```

#### 데이터베이스 연결 오류

**증상**: `Can't connect to MySQL server`

**해결**:
```bash
# Docker MySQL 컨테이너 상태 확인
docker-compose ps mysql

# MySQL 로그 확인
docker-compose logs mysql

# MySQL 재시작
docker-compose restart mysql
```

#### 포트 충돌

**증상**: 포트가 이미 사용 중

**해결**:
```bash
# 포트 사용 확인 (Windows)
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# 포트 사용 확인 (Linux/Mac)
lsof -i :3000
lsof -i :8000

# docker-compose.yml에서 포트 변경 가능
```

#### Agent 서비스 오류

**증상**: Agent가 초기화되지 않음

**해결**:
```bash
# Agent 로그 확인
docker-compose logs agent

# Chrome 브라우저 설치 확인
docker-compose exec agent google-chrome --version

# Playwright 브라우저 설치 확인
docker-compose exec agent playwright --version
```

#### 메모리 부족

**증상**: 컨테이너가 자주 재시작됨

**해결**:
```bash
# Docker Desktop 메모리 할당 증가
# Docker Desktop → Settings → Resources → Memory

# 불필요한 컨테이너 정리
docker system prune -f
```

### 9.2 에러 확인 가이드

#### 실시간 로그 확인

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

#### 최근 에러만 확인

```bash
# 최근 100줄 로그
docker-compose logs --tail=100 agent

# 에러만 필터링 (PowerShell)
docker-compose logs agent | Select-String -Pattern "Error|Exception|Failed|Traceback"

# 에러만 필터링 (Linux/Mac)
docker-compose logs agent | grep -i "error\|exception\|failed\|traceback"
```

#### 특정 시간대 로그 확인

```bash
# 최근 10분간 로그
docker-compose logs --since 10m agent

# 특정 시간 이후 로그
docker-compose logs --since 2024-12-29T16:00:00 agent
```

### 9.3 MySQL 문제 해결

#### 연결 거부

**증상**: `ERROR 2003 (HY000): Can't connect to MySQL server`

**해결**:
```bash
# MySQL 서비스 상태 확인
docker-compose ps mysql

# MySQL 서비스 시작
# Windows: net start MySQL80
# Mac: brew services start mysql
# Ubuntu: sudo systemctl start mysql
```

#### 인증 실패

**증상**: `ERROR 1045 (28000): Access denied`

**해결**:
- 비밀번호 확인
- 환경 변수의 데이터베이스 정보 확인
- Root 비밀번호 재설정 (필요시)

#### 데이터베이스가 존재하지 않음

**증상**: `ERROR 1049 (42000): Unknown database`

**해결**:
```bash
# 데이터베이스 초기화 스크립트 재실행
docker-compose exec mysql mysql -u root -prootpassword123 < setup_database/04_database_setup.sql
```

### 9.4 크롤링 문제 해결

#### Playwright 브라우저 찾을 수 없음

**증상**:
```
BrowserType.launch: Executable doesn't exist at /tmp/.cache/ms-playwright/...
```

**해결**:
```dockerfile
# Dockerfile에서 PLAYWRIGHT_BROWSERS_PATH 설정
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

RUN playwright install chromium
```

#### 구글 뉴스 셀렉터 실패

**증상**: 모든 CSS 셀렉터 실패

**해결**: RSS 피드로 전환하여 안정적인 URL 수집

#### 타임아웃 오류

**증상**: 5분 타임아웃 에러

**해결**:
1. URL 필터링 강화 (실제 기사만 수집)
2. 타임아웃 시간 조정 (필요시)
3. 재시도 로직 추가

---

## 10. 참고 자료

### 10.1 API 문서

#### 주요 엔드포인트

**POST /api/agents/analyze**
뉴스 감정 분석 요청

```json
{
  "keyword": "인공지능",
  "sources": ["네이버", "구글"],
  "max_articles": 50
}
```

**GET /api/analysis/{session_id}**
분석 결과 조회

**GET /api/analysis/sessions**
분석 세션 목록 조회

**Agent 서비스 엔드포인트**:
- `GET /health`: Agent 헬스체크
- `POST /analyze`: 뉴스 분석 실행
- `POST /analyze-sentiment`: 자연어 질의 분석

자세한 API 문서는 http://localhost:8000/docs 에서 확인하세요.

### 10.2 보안 가이드라인

이 프로젝트는 한국 개인정보보호법 및 ISMS-P 수준의 보안 가이드라인을 따릅니다.

#### 주요 보안 사항

1. **API 키 관리**
   - 환경 변수에서만 읽기
   - 로그에 절대 노출하지 않음
   - .env 파일을 .gitignore에 추가

2. **입력 검증**
   - 모든 사용자 입력 검증
   - SQL Injection 방지
   - XSS 방지

3. **크롤링**
   - robots.txt 준수
   - Rate Limit 준수
   - User-Agent 설정

4. **에러 처리**
   - 민감한 정보를 에러 메시지에 포함하지 않음
   - 일반화된 에러 메시지 제공

### 10.3 테스트

#### Backend 테스트

```bash
cd backend
pytest tests/ -v
```

#### Frontend 테스트

```bash
cd frontend
npm run test
npm run lint
```

### 10.4 배포

#### GitHub Actions를 통한 자동 배포

1. GitHub Secrets 설정:
   - `OPENAI_API_KEY`: OpenAI API 키
   - `PRODUCTION_HOST`: 프로덕션 서버 호스트
   - `PRODUCTION_USER`: SSH 사용자명
   - `PRODUCTION_SSH_KEY`: SSH 개인 키
   - `SLACK_WEBHOOK`: Slack 알림 웹훅 (선택사항)

2. main 브랜치에 푸시하면 자동 배포 실행

#### 수동 배포

```bash
# 프로덕션 환경 변수 설정
cp .env.example .env.production

# 프로덕션 빌드 및 배포
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 10.5 외부 자료

- **LangChain 공식 문서**: https://docs.langchain.com/
- **Playwright 공식 문서**: https://playwright.dev/python/
- **FastAPI 공식 문서**: https://fastapi.tiangolo.com/
- **Next.js 공식 문서**: https://nextjs.org/docs
- **OpenAI API 문서**: https://platform.openai.com/docs/
- **MySQL 공식 문서**: https://dev.mysql.com/doc/

### 10.6 커뮤니티 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **강의 Q&A**: 강의 관련 질문
- **Slack**: #ai-agents-support

---

## 부록

### A. 환경 변수 목록

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-your-openai-api-key-here

# 데이터베이스 설정
MYSQL_ROOT_PASSWORD=your-secure-password
MYSQL_PASSWORD=your-secure-password
MYSQL_DATABASE=news_sentiment

# 프로덕션 보안
SECRET_KEY=your-super-secret-key-change-this-in-production

# 선택적 API 키
GEMINI_API_KEY=your_gemini_api_key
FIRECRAWL_API_KEY=your_firecrawl_api_key
```

### B. 주요 명령어 모음

```bash
# 전체 스택 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 재시작
docker-compose restart agent backend

# 서비스 중지
docker-compose stop

# 컨테이너 제거
docker-compose down

# 재빌드
docker-compose build --no-cache

# MySQL 접속
docker-compose exec mysql mysql -u newsuser -p news_sentiment
```

### C. 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2024-12-29 | 1.0 | Selenium 기반 초기 구현 |
| 2024-12-30 | 1.1 | 네이버/구글 스크래퍼 분리 |
| 2024-12-30 | 2.0 | Playwright + 병렬처리 도입 |
| 2025-12-29 | 2.1 | 네이버 스크래핑 오류 수정 |
| 2025-12-29 | 2.2 | 본문 추출 오류 수정 |
| 2025-12-29 | 2.3 | URL 필터링 강화 |

---

**작성일**: 2025년 12월  
**최종 업데이트**: 2025년 12월 29일  
**버전**: 2.3

---

🎓 **AI Agent 기반 뉴스 감정 분석 시스템 완전 가이드**

이 문서는 프로젝트의 모든 문서를 통합한 완전한 가이드입니다.  
프로젝트 시작부터 문제 해결까지 모든 정보가 포함되어 있습니다.
