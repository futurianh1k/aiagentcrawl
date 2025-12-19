# 🤖 News Sentiment AI Agent System

AI Agent 기반 뉴스 감정 분석 시스템 - 4일차 강의용 완전한 소스코드 프로젝트

## 📋 프로젝트 개요

이 프로젝트는 **LangChain AI Agent**를 활용한 실시간 뉴스 감정 분석 시스템입니다. FastAPI 백엔드와 Next.js 프론트엔드로 구성되어 있으며, Docker를 통한 컨테이너화와 GitHub Actions를 통한 CI/CD 파이프라인을 제공합니다.

### 🎯 주요 기능

- **🤖 AI Agent 기반 분석**: LangChain ReAct 패턴으로 구현된 멀티 에이전트 시스템
- **📊 실시간 감정 분석**: OpenAI API를 활용한 뉴스 기사 및 댓글 감정 분석
- **🔍 지능형 뉴스 수집**: 네이버 뉴스와 구글 뉴스 크롤링 지원
- **📈 데이터 시각화**: Recharts를 활용한 감정 분포 및 키워드 클라우드
- **🚀 확장 가능한 아키텍처**: 마이크로서비스 아키텍처 및 컨테이너화
- **⚡ 고성능 처리**: 비동기 처리 및 Redis 캐싱

### 🏗️ 기술 스택

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
- **Selenium** - 웹 크롤링 (네이버/구글 뉴스)
- **LangChain** - AI Agent 프레임워크
- **OpenAI/Gemini** - 감성 분석

#### DevOps
- **Docker** & **Docker Compose** - 컨테이너화
- **GitHub Actions** - CI/CD 파이프라인
- **Nginx** - 리버스 프록시 (선택사항)

## 🚀 빠른 시작

### 1. 필수 요구사항

- Docker & Docker Compose
- Node.js 18+ (로컬 개발시)
- Python 3.11+ (로컬 개발시)
- OpenAI API 키

### 2. 프로젝트 클론 및 설정

```bash
# 프로젝트 클론
git clone <repository-url>
cd aiagent

# 환경 변수 설정
cp .env.example .env
```

### 3. 환경 변수 구성

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

### 4. Docker Compose로 전체 스택 실행

```bash
# 전체 스택 시작 (MySQL, Redis, Agent, Backend, Frontend)
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 상태 확인
docker-compose ps
```

### 5. 애플리케이션 접속

- **프론트엔드**: http://localhost:3000
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Agent 서비스**: http://localhost:8001

## 📁 프로젝트 구조

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
├── docker-compose.yml         # 전체 스택 오케스트레이션
├── .env.example              # 환경 변수 템플릿
└── README.md                 # 이 문서
```

## 🔧 개발 환경 설정

### Backend 로컬 개발

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

### Frontend 로컬 개발

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

### Agent 로컬 개발

```bash
# Agent 테스트
python -m agent.news_agent

# Agent 서버 실행
python -m agent.server
```

## 🧪 테스트

### Backend 테스트

```bash
cd backend
pytest tests/ -v
```

### Frontend 테스트

```bash
cd frontend
npm run test
npm run lint
```

## 🚀 배포

### GitHub Actions를 통한 자동 배포

1. GitHub Secrets 설정:
   - `OPENAI_API_KEY`: OpenAI API 키
   - `PRODUCTION_HOST`: 프로덕션 서버 호스트
   - `PRODUCTION_USER`: SSH 사용자명
   - `PRODUCTION_SSH_KEY`: SSH 개인 키
   - `SLACK_WEBHOOK`: Slack 알림 웹훅 (선택사항)

2. main 브랜치에 푸시하면 자동 배포 실행

### 수동 배포

```bash
# 프로덕션 환경 변수 설정
cp .env.example .env.production

# 프로덕션 빌드 및 배포
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📊 AI Agent 시스템 아키텍처

### Agent 구성요소

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

### ReAct 패턴 구현

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

## 🔍 API 문서

### 주요 엔드포인트

#### POST /api/agents/analyze
뉴스 감정 분석 요청

```json
{
  "keyword": "인공지능",
  "sources": ["네이버", "구글"],
  "max_articles": 50
}
```

#### GET /api/analysis/{session_id}
분석 결과 조회

#### GET /api/analysis/sessions
분석 세션 목록 조회

#### Agent 서비스 엔드포인트

- `GET /health`: Agent 헬스체크
- `POST /analyze`: 뉴스 분석 실행
- `POST /analyze-sentiment`: 자연어 질의 분석

자세한 API 문서는 http://localhost:8000/docs 에서 확인하세요.

## 🔒 보안 가이드라인

이 프로젝트는 한국 개인정보보호법 및 ISMS-P 수준의 보안 가이드라인을 따릅니다.

### 주요 보안 사항

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

자세한 내용은 `PROJECT_REVIEW.md`를 참조하세요.

## 🤝 기여 방법

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🆘 문제 해결

### 일반적인 문제들

1. **OpenAI API 키 오류**
   - `.env` 파일의 `OPENAI_API_KEY` 확인
   - API 키 유효성 및 크레딧 잔액 확인

2. **데이터베이스 연결 오류**
   - Docker MySQL 컨테이너 상태 확인
   - 환경 변수의 데이터베이스 정보 확인

3. **포트 충돌**
   - 3000, 8000, 8001, 3306 포트 사용 여부 확인
   - `docker-compose.yml`에서 포트 변경 가능

4. **Agent 서비스 오류**
   - Chrome 브라우저 설치 확인
   - Agent 로그 확인: `docker-compose logs agent`

5. **메모리 부족**
   - Docker Desktop 메모리 할당 증가
   - 불필요한 컨테이너 정리

### 로그 확인

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend
docker-compose logs agent
docker-compose logs mysql
```

## 📚 문서

- [QUICK_START.md](QUICK_START.md): 빠른 시작 가이드
- [DOCKER_SETUP.md](DOCKER_SETUP.md): 상세한 Docker 설정 가이드
- [PROJECT_REVIEW.md](PROJECT_REVIEW.md): 프로젝트 구조 및 리팩토링 계획
- [AGENT_REFACTORING_SUMMARY.md](AGENT_REFACTORING_SUMMARY.md): Agent 리팩토링 요약
- [agent/README.md](agent/README.md): Agent 사용 가이드

## 📞 지원

문제가 있거나 질문이 있으시면 다음 방법으로 연락해주세요:

- GitHub Issues: 버그 리포트 및 기능 요청
- 이메일: your-email@example.com
- 슬랙: #ai-agents-support

---

🎓 **4일차 AI Agent 강의용 프로젝트**

이 프로젝트는 AI Agent의 실제 구현 방법을 학습하기 위한 교육용 자료입니다. 
실제 프로덕션 환경에서 사용하기 전에 보안 및 성능 최적화를 권장합니다.
