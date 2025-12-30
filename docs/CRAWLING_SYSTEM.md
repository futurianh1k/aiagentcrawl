# 뉴스 크롤링 시스템 개발 기록

## 개요

뉴스 감정 분석 시스템의 핵심 구성요소인 크롤링 시스템의 개발 과정과 아키텍처를 문서화합니다.

**작성일**: 2024년 12월 30일  
**버전**: 2.0 (Playwright + 병렬처리)

---

## 1. 시스템 진화 과정

### Phase 1: Selenium 기반 순차 크롤링 (초기)

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

### Phase 2: Playwright + 병렬처리 (현재)

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

---

## 2. 아키텍처

### 파일 구조

```
agent/tools/news_scraper/
├── __init__.py              # 패키지 초기화 및 export
├── models.py                # NewsArticle, Comment 데이터 모델
│
├── # Selenium 기반 (폴백용)
├── base_scraper.py          # Selenium 베이스 클래스
├── naver_scraper.py         # 네이버 뉴스 (Selenium)
├── google_scraper.py        # 구글 뉴스 (Selenium)
├── scraper.py               # 통합 인터페이스 (Selenium)
│
└── # Playwright 기반 (메인)
    ├── playwright_base.py   # Playwright 베이스 클래스
    ├── playwright_naver.py  # 네이버 뉴스 (Playwright)
    ├── playwright_google.py # 구글 뉴스 (Playwright + RSS)
    └── playwright_scraper.py # 병렬처리 통합 스크래퍼
```

### 클래스 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                  PlaywrightNewsScraper                      │
│              (asyncio.gather 병렬처리)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ + search_news_parallel()    # 병렬 검색             │    │
│  │ + extract_articles_parallel() # 병렬 추출           │    │
│  │ + scrape_all()              # 전체 파이프라인        │    │
│  │ + cleanup()                 # 리소스 정리            │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│ PlaywrightNaverScraper │    │ PlaywrightGoogleScraper │
│  extends                │    │  extends                │
│  PlaywrightBaseScraper  │    │  PlaywrightBaseScraper  │
└─────────────────────┘       └─────────────────────┘
          │                               │
          └───────────────┬───────────────┘
                          ▼
              ┌─────────────────────┐
              │ PlaywrightBaseScraper │
              │  (추상 베이스 클래스)  │
              │  + setup()           │
              │  + cleanup()         │
              │  + new_page()        │
              │  + extract_text_by_selectors() │
              └─────────────────────┘
```

---

## 3. 주요 기술 스택

### Playwright vs Selenium 비교

| 항목 | Selenium | Playwright |
|------|----------|------------|
| **속도** | 느림 | 2-3배 빠름 |
| **비동기** | 제한적 (threading) | 네이티브 async/await |
| **자동 대기** | 수동 (explicit wait) | 자동 (auto-waiting) |
| **메모리** | 높음 | 낮음 |
| **브라우저 설치** | WebDriver 별도 관리 | `playwright install` 통합 |
| **병렬처리** | 복잡 | 간단 (asyncio.gather) |

### 사용된 기술

- **Playwright** (v1.40+): 브라우저 자동화
- **asyncio**: 비동기 프로그래밍
- **RSS 피드**: 구글 뉴스 URL 수집 (안정적)
- **Semaphore**: 동시 처리 수 제한

---

## 4. 구현 세부사항

### 4.1 병렬 검색

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

### 4.2 병렬 기사 추출 (Semaphore로 동시 처리 제한)

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

### 4.3 구글 뉴스 RSS 피드 활용

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

### 4.4 불필요한 리소스 차단 (속도 향상)

```python
# 이미지, 폰트 로딩 차단
await context.route("**/*.{png,jpg,jpeg,gif,svg,webp,ico}", lambda route: route.abort())
await context.route("**/*.woff*", lambda route: route.abort())
```

---

## 5. Docker 설정

### Dockerfile 핵심 설정

```dockerfile
# Playwright 브라우저 전역 설치
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers

RUN pip install --no-cache-dir playwright>=1.40.0 \
    && mkdir -p /opt/playwright-browsers \
    && playwright install chromium \
    && playwright install-deps chromium \
    && chmod -R 755 /opt/playwright-browsers
```

**중요**: `PLAYWRIGHT_BROWSERS_PATH`를 빌드 시와 런타임 시 동일하게 설정해야 합니다.

---

## 6. 에러 처리 및 폴백

### 자동 폴백 로직

```python
if PLAYWRIGHT_AVAILABLE:
    # Playwright 병렬처리 사용
    playwright_scraper = PlaywrightNewsScraper()
    articles = await playwright_scraper.scrape_all(keyword, sources, max_articles)
else:
    # Selenium 순차처리 폴백
    selenium_scraper = NewsScraperTool()
    articles = await selenium_sequential_scrape(...)
```

### 타임아웃 설정

| 구간 | 타임아웃 |
|------|----------|
| 전체 크롤링 | 3분 (Playwright) / 2분 (Selenium) |
| 개별 페이지 로드 | 30초 |
| API 호출 (Backend → Agent) | 10분 |

---

## 7. 성능 측정

### 테스트 조건
- 키워드: "테슬라"
- 소스: 네이버 + 구글
- 기사 수: 소스당 5개 (총 10개)

### 결과

| 구현 방식 | 검색 시간 | 추출 시간 | 총 시간 |
|----------|----------|----------|---------|
| Selenium 순차 | ~60초 | ~40초 | **~100초** |
| Playwright 병렬 | ~10초 | ~15초 | **~25초** |
| **속도 향상** | 6배 | 2.7배 | **4배** |

---

## 8. 트러블슈팅

### 8.1 Playwright 브라우저 찾을 수 없음

**증상**:
```
BrowserType.launch: Executable doesn't exist at /tmp/.cache/ms-playwright/...
```

**원인**: Docker에서 root로 설치 후 appuser로 실행 시 경로 불일치

**해결**:
```dockerfile
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
```

### 8.2 Chrome WebDriver 권한 오류

**증상**:
```
Permission denied: '/home/appuser'
```

**해결**: ChromeDriver를 `/usr/local/bin/`에 직접 설치

### 8.3 구글 뉴스 셀렉터 실패

**증상**: 모든 CSS 셀렉터 실패

**해결**: RSS 피드로 전환하여 안정적인 URL 수집

---

## 9. 향후 개선 계획

1. **캐싱**: 동일 키워드 재검색 시 캐시된 결과 반환
2. **Retry 로직**: 일시적 오류 시 자동 재시도
3. **프록시 지원**: IP 차단 방지
4. **더 많은 소스**: 다음, 네이트, 연합뉴스 등 추가

---

## 10. 참고 자료

- [Playwright Python 공식 문서](https://playwright.dev/python/)
- [asyncio 공식 문서](https://docs.python.org/3/library/asyncio.html)
- [구글 뉴스 RSS 피드](https://news.google.com/rss)
- [Selenium 공식 문서](https://www.selenium.dev/documentation/)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 |
|------|------|----------|
| 2024-12-29 | 1.0 | Selenium 기반 초기 구현 |
| 2024-12-30 | 1.1 | 네이버/구글 스크래퍼 분리 |
| 2024-12-30 | 2.0 | Playwright + 병렬처리 도입 |

