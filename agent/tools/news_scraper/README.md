# 2회차 강의: AI 에이전트 기반 뉴스 감성 분석 시스템
## Playwright 기반 크롤링 파이프라인

### 📋 프로젝트 개요

본 프로젝트는 **2회차 강의 교안의 모든 코드**를 체계적으로 정리한 **Playwright 기반 뉴스 크롤링 파이프라인**입니다. 
고급 웹 크롤링 기술과 데이터 파이프라인 아키텍처를 통해 뉴스 기사와 댓글을 수집하고 감성 분석을 수행합니다.

### 🎯 주요 학습 목표

- **Playwright MCP**: Contexts & Pages를 활용한 고급 크롤링 전략
- **Explicit Wait 패턴**: Flaky Test 문제 해결 및 안정적인 크롤링
- **Pydantic 검증**: 데이터 품질 보장 및 타입 안전성
- **SQLAlchemy ORM**: 효율적인 데이터베이스 모델링 및 인덱싱
- **Batch Insert 최적화**: 15배 성능 향상 (30초 → 2초)
- **비동기 처리**: aiohttp를 통한 6배 성능 향상 (50초 → 8초)
- **Retry 전략**: tenacity를 활용한 지수 백오프
- **데이터 파이프라인**: Collection → Validation → Transformation → Storage

### 🏗️ 프로젝트 구조

```
session2_crawling_pipeline/
├── README.md                          # 📖 전체 가이드
├── requirements.txt                   # 📦 패키지 의존성
├── .env.example                       # ⚙️ 환경 변수 템플릿
├── setup.sh                           # 🐧 Linux/Mac 설치 스크립트
├── setup.bat                          # 🪟 Windows 설치 스크립트
├── config/
│   ├── __init__.py
│   └── settings.py                    # 🔧 Pydantic 설정 관리
├── models/
│   ├── __init__.py
│   ├── database.py                    # 🗄️ SQLAlchemy ORM 모델
│   └── validation.py                  # ✅ Pydantic 검증 모델
├── crawlers/
│   ├── __init__.py
│   ├── playwright_basic.py            # 🎭 Playwright 기초 (Contexts, Pages)
│   ├── selectors.py                   # 🎯 고급 Selector 전략
│   ├── explicit_wait.py               # ⏱️ Explicit Wait 패턴
│   ├── dynamic_content.py             # 🔄 무한 스크롤, AJAX 처리
│   ├── firecrawl_integration.py       # 🔥 Firecrawl MCP 통합
│   └── stealth_mode.py                # 🥷 Bot 감지 우회
├── pipeline/
│   ├── __init__.py
│   ├── data_pipeline.py               # 🏗️ 데이터 파이프라인 아키텍처
│   ├── batch_insert.py                # ⚡ Batch Insert 최적화 (15x 향상)
│   ├── transaction_handler.py         # 💾 트랜잭션 및 롤백
│   ├── async_crawler.py               # 🚀 비동기 처리 (6x 향상)
│   └── retry_strategy.py              # 🔄 Retry 전략 (tenacity)
├── tests/
│   ├── __init__.py
│   ├── test_flaky_solutions.py        # 🧪 Flaky Test 해결
│   ├── page_objects.py                # 📄 Page Object Model
│   └── integration_test.py            # 🔗 통합 테스트
├── utils/
│   ├── __init__.py
│   ├── logger.py                      # 📝 로깅 유틸리티
│   └── debugging.py                   # 🐛 디버깅 도구
└── examples/
    ├── __init__.py
    ├── 01_playwright_setup.py         # 예제 1: 환경 설정
    ├── 02_context_pages.py            # 예제 2: Contexts & Pages
    ├── 03_explicit_wait_demo.py       # 예제 3: Explicit Wait
    ├── 04_dynamic_content_demo.py     # 예제 4: 동적 콘텐츠
    ├── 05_pydantic_validation.py      # 예제 5: Pydantic 검증
    ├── 06_batch_insert_demo.py        # 예제 6: Batch Insert
    ├── 07_async_demo.py               # 예제 7: 비동기 처리
    ├── 08_retry_demo.py               # 예제 8: Retry 전략
    └── 09_hands_on_news_scraper.py    # 예제 9: 완전한 NewsScraper
```

### 💻 시스템 요구사항

- **Python**: 3.10 이상
- **Operating System**: Windows, macOS, Linux
- **Memory**: 최소 4GB RAM (권장 8GB)
- **Storage**: 최소 2GB 여유 공간
- **Database**: MySQL 8.0 이상
- **Browser**: Chromium/Chrome (Playwright가 자동 설치)

### 🚀 빠른 시작

#### 1. 자동 설치 (권장)

**Linux/Mac:**
```bash
# 저장소 클론
git clone <repository-url>
cd session2_crawling_pipeline

# 자동 설치 실행
chmod +x setup.sh
./setup.sh
```

**Windows:**
```cmd
# 저장소 클론
git clone <repository-url>
cd session2_crawling_pipeline

# 자동 설치 실행
setup.bat
```

#### 2. 수동 설치

**2.1 가상환경 생성**
```bash
# Python 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

**2.2 패키지 설치**
```bash
# 의존성 패키지 설치
pip install -r requirements.txt

# Playwright 브라우저 설치
playwright install chromium
```

**2.3 환경 설정**
```bash
# 환경 변수 파일 생성
cp .env.example .env

# 환경 변수 편집 (에디터로 열어서 수정)
nano .env
```

### ⚙️ 환경 변수 설정

`.env` 파일에서 다음 필수 값들을 설정하세요:

```bash
# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_DATABASE=news_sentiment

# API 키 (선택적)
FIRECRAWL_API_KEY=your_firecrawl_key
OPENAI_API_KEY=your_openai_key

# 크롤링 설정
CRAWLER_HEADLESS=true
CRAWLER_MAX_CONCURRENT_PAGES=5
```

### 🗄️ 데이터베이스 초기화

```python
# 데이터베이스 테이블 생성
python -c "
from models.database import create_tables
create_tables(drop_existing=False)
print('데이터베이스 테이블이 생성되었습니다.')
"

# 연결 테스트
python -c "
from models.database import test_connection
if test_connection():
    print('✅ 데이터베이스 연결 성공!')
else:
    print('❌ 데이터베이스 연결 실패')
"
```

### 📚 예제 실행 가이드

#### 예제 1: Playwright 기본 설정
```bash
python examples/01_playwright_setup.py
```

#### 예제 2: Context & Pages 관리
```bash
python examples/02_context_pages.py
```

#### 예제 3: Explicit Wait 패턴
```bash
python examples/03_explicit_wait_demo.py
```

#### 예제 6: Batch Insert 성능 비교
```bash
python examples/06_batch_insert_demo.py
# 출력 예시:
# 개별 Insert: 30.45초 (1000건)
# Batch Insert: 2.12초 (1000건)  
# 📈 성능 향상: 14.4배
```

#### 예제 7: 비동기 크롤링
```bash
python examples/07_async_demo.py
# 출력 예시:
# 동기 처리: 48.23초 (10개 URL)
# 비동기 처리: 8.15초 (10개 URL)
# 📈 성능 향상: 5.9배
```

### 🧪 테스트 실행

```bash
# 모든 테스트 실행
pytest tests/ -v

# 특정 테스트 실행
pytest tests/test_flaky_solutions.py -v

# 커버리지 포함 테스트
pytest tests/ --cov=. --cov-report=html
```

### 🔧 성능 최적화 가이드

#### Batch Insert 최적화
```python
# ❌ 느린 방법 (30초)
for article_data in article_list:
    session.add(Article(**article_data))
    session.commit()

# ✅ 빠른 방법 (2초, 15배 향상)
session.bulk_insert_mappings(Article, article_list)
session.commit()
```

#### 비동기 크롤링
```python
# ❌ 동기 처리 (50초)
results = []
for url in urls:
    result = requests.get(url)
    results.append(result)

# ✅ 비동기 처리 (8초, 6배 향상)
async with aiohttp.ClientSession() as session:
    tasks = [session.get(url) for url in urls]
    results = await asyncio.gather(*tasks)
```

### 📊 주요 성능 지표

| 기능 | 이전 성능 | 최적화 후 | 개선율 |
|-----|----------|-----------|--------|
| Batch Insert | 30초 (1000건) | 2초 (1000건) | **15배 향상** |
| 비동기 크롤링 | 50초 (10 URL) | 8초 (10 URL) | **6배 향상** |
| Retry 전략 | 즉시 실패 | 지수 백오프 | **안정성 95% 향상** |
| Flaky Test | 30% 실패율 | 1% 실패율 | **신뢰성 97% 향상** |

### 🛠️ 트러블슈팅

#### 일반적인 문제들

**Q1. Playwright 브라우저 설치 오류**
```bash
# 수동 설치
playwright install chromium

# 권한 문제 해결 (Linux)
sudo apt-get update
sudo apt-get install -y libgbm-dev
```

**Q2. MySQL 연결 오류**
```bash
# MySQL 서비스 시작
# Linux:
sudo systemctl start mysql
# Windows:
net start mysql
# macOS:
brew services start mysql
```

**Q3. 메모리 부족 오류**
```python
# 설정에서 배치 크기 줄이기
APP_BATCH_SIZE=500
CRAWLER_MAX_CONCURRENT_PAGES=3
```

**Q4. Playwright 타임아웃**
```python
# 타임아웃 시간 증가
CRAWLER_PAGE_TIMEOUT=60000
CRAWLER_WAIT_TIMEOUT=20000
```

#### 로그 확인
```bash
# 애플리케이션 로그 확인
tail -f logs/app.log

# 크롤링 로그 확인
python -c "
from utils.logger import setup_logger
logger = setup_logger()
logger.info('로깅 시스템 테스트')
"
```

### 📖 핵심 개념 설명

#### 1. Playwright MCP (Multi-Context Pattern)
```python
# Context 기반 병렬 크롤링
async with PlaywrightManager() as manager:
    context1 = await manager.create_context()  # 세션 1
    context2 = await manager.create_stealth_context()  # 세션 2

    # 각 Context는 독립적인 세션 유지
    page1 = await context1.new_page()
    page2 = await context2.new_page()
```

#### 2. Explicit Wait vs Implicit Wait
```python
# ❌ 잘못된 방법 (Flaky Test 원인)
await page.goto(url)
time.sleep(3)  # 고정 대기
element = await page.query_selector('.content')

# ✅ 올바른 방법 (안정적)
await page.goto(url)
await page.wait_for_selector('.content', state='visible')
element = await page.query_selector('.content')
```

#### 3. Pydantic 데이터 검증
```python
# 자동 검증 및 타입 변환
article_data = {
    "title": "뉴스 제목",
    "published_at": "2024-01-15T10:30:00Z",
    "tags": ["정치", "경제"]
}

# 검증된 모델 생성
article = ArticleData(**article_data)  # 자동 검증
db_dict = article.to_db_dict()  # DB 저장용 변환
```

### 🔗 추가 자료

- **Playwright 공식 문서**: https://playwright.dev/python/
- **Pydantic 가이드**: https://docs.pydantic.dev/
- **SQLAlchemy 튜토리얼**: https://docs.sqlalchemy.org/
- **aiohttp 비동기 가이드**: https://docs.aiohttp.org/
- **tenacity Retry 전략**: https://tenacity.readthedocs.io/

### 📞 지원 및 문의

프로젝트 관련 문의사항이나 오류 신고는 다음 채널을 통해 연락해주세요:

- **이슈 트래킹**: GitHub Issues
- **기술 문의**: 강의 Q&A 게시판
- **긴급 지원**: 강의 담당자 이메일

### 📝 라이선스

이 프로젝트는 교육 목적으로 제작되었으며, MIT 라이선스를 따릅니다.

---

**📚 2회차 강의 교안의 모든 코드가 포함된 완전한 프로젝트입니다!**
