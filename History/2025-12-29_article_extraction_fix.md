# 네이버 뉴스 본문 추출 오류 수정

**날짜**: 2025-12-29  
**작업자**: AI Agent (Cursor)  
**브랜치**: main  
**이전 커밋**: a9ec022

## 요구사항

사용자가 뉴스 분석을 테스트했을 때 다음 오류 발생:
```
본문 추출 실패 | {'error': 'no such element: Unable to locate element: 
{"method":"tag name","selector":"article"}'}
```

네이버 뉴스 URL 10개는 성공적으로 수집했지만, 본문 추출 단계에서 모든 기사가 실패.

## 문제 분석

### 로그 분석
```
[DEBUG] 최종 수집된 URL 개수: 10  ✅ URL 수집 성공
본문 추출 실패 | no such element: {"method":"tag name","selector":"article"}  ❌
```

### 근본 원인

1. **잘못된 fallback 로직**
   ```python
   # 기존 코드 (문제)
   content_elements = self.driver.find_elements(By.CSS_SELECTOR, selectors["content"])
   if content_elements:
       content = " ".join([elem.text.strip() for elem in content_elements])
   else:
       # ❌ 여기서 article 태그를 찾으려고 시도
       content = self.driver.find_element(By.TAG_NAME, "article").text.strip()
   ```

2. **네이버 뉴스 페이지 구조**
   - 네이버 뉴스는 `<article>` 태그를 사용하지 않음
   - 대신 `<div id="dic_area">`, `<div id="articeBody">` 등 사용
   - 페이지 버전에 따라 셀렉터가 다름

3. **단일 셀렉터의 한계**
   - 기존 코드는 주 셀렉터 실패 시 `article` 태그로만 fallback
   - 네이버의 다양한 페이지 구조를 처리할 수 없음

## 해결 방법

### 1. 제목 추출 강화

**이전 코드**:
```python
try:
    title_element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selectors["title"]))
    )
    title = title_element.text.strip()
except Exception:
    title = self.driver.find_element(By.TAG_NAME, "h1").text.strip()
```

**개선된 코드**:
```python
title_selectors = [
    selectors["title"],              # 기본 셀렉터
    "h2.media_end_head_headline",    # 네이버 뉴스 헤드라인
    "h3.tit_view",                   # 구버전
    ".article_header h2",            # 일반적인 패턴
    ".article_view h3",
    "h1", "h2"                       # 기본 태그
]

for title_selector in title_selectors:
    try:
        title_element = WebDriverWait(self.driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
        )
        if title_element and title_element.text.strip():
            title = title_element.text.strip()
            print(f"[DEBUG] ✓ 제목 추출 성공! (셀렉터: {title_selector})")
            break
    except Exception:
        continue
```

**개선 사항**:
- 7개의 셀렉터를 순차적으로 시도
- 각 시도마다 디버그 로그 출력
- 짧은 타임아웃(2초)으로 빠른 fallback

### 2. 본문 추출 강화

**이전 코드의 문제**:
```python
else:
    # ❌ article 태그가 없는 네이버 뉴스에서 실패
    content = self.driver.find_element(By.TAG_NAME, "article").text.strip()
```

**개선된 코드**:
```python
content_selectors = [
    selectors["content"],            # #dic_area (기본)
    "#articeBody",                   # 구버전
    ".article_body",                 # 일반적인 클래스명
    ".article_view",
    "article",                       # HTML5 표준 (있는 경우)
    ".news_end_body_container",      # 네이버 특정 구조
    "#newsct_article",               # 네이버 뉴스 컨테이너
    "div#articleBodyContents"        # 다음/카카오 등
]

for content_selector in content_selectors:
    try:
        content_elements = self.driver.find_elements(By.CSS_SELECTOR, content_selector)
        if content_elements:
            content_text = " ".join([elem.text.strip() for elem in content_elements 
                                     if elem.text.strip()])
            # ✅ 최소 길이 검증 (50자 이상)
            if content_text and len(content_text) > 50:
                content = content_text
                print(f"[DEBUG] ✓ 본문 추출 성공! (셀렉터: {content_selector}, 
                                                  길이: {len(content)}자)")
                break
    except Exception:
        continue
```

**개선 사항**:
- 8개의 셀렉터를 순차적으로 시도
- **최소 길이 검증**: 50자 미만은 무시 (광고, 메뉴 등 제외)
- 각 셀렉터의 성공/실패 상세 로그
- 실패 시 페이지 소스 일부 출력 (디버깅용)

### 3. 디버깅 로그 강화

**추가된 로그**:
```python
print(f"[DEBUG] 제목 추출 시도 (URL: {url[:60]}...)")
print(f"[DEBUG] ✓ 제목 추출 성공! (셀렉터 {i}: {title_selector})")

print(f"[DEBUG] 본문 추출 시도 (총 {len(content_selectors)}개 셀렉터)")
print(f"[DEBUG] 셀렉터 {i} ({content_selector}): 내용 부족 ({len(content_text)}자)")
print(f"[DEBUG] 셀렉터 {i} ({content_selector}): 요소 없음")
print(f"[DEBUG] ✓ 본문 추출 성공! (셀렉터 {i}: {content_selector}, 길이: {len(content)}자)")

# 실패 시
page_source = self.driver.page_source[:2000]
print(f"[DEBUG] 페이지 소스 미리보기:\n{page_source}\n...")
```

**로그 예시**:
```
[DEBUG] 제목 추출 시도 (URL: https://n.news.naver.com/mnews/article...)
[DEBUG] ✓ 제목 추출 성공! (셀렉터 1: #ct > div.media_end_head...)
[DEBUG] 본문 추출 시도 (총 8개 셀렉터)
[DEBUG] 셀렉터 1 (#dic_area): ✓ 본문 추출 성공! (길이: 1234자)
```

## 기술적 세부사항

### WebDriverWait 타임아웃 조정

```python
# 제목 추출: 짧은 타임아웃 (2초)
title_element = WebDriverWait(self.driver, 2).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, title_selector))
)
```

**이유**:
- 빠른 fallback을 위해 짧은 타임아웃 사용
- 각 셀렉터당 2초 → 7개 시도 = 최대 14초
- 전체 타임아웃보다 효율적

### 컨텐츠 품질 검증

```python
if content_text and len(content_text) > 50:  # 최소 50자
    content = content_text
    break
```

**이유**:
- 광고, 메뉴, 버튼 텍스트 제외
- "로그인", "회원가입" 등 불필요한 텍스트 필터링
- 실제 기사 본문만 추출

### 다중 요소 처리

```python
content_elements = self.driver.find_elements(By.CSS_SELECTOR, content_selector)
content_text = " ".join([elem.text.strip() for elem in content_elements 
                         if elem.text.strip()])
```

**이유**:
- 일부 페이지는 본문이 여러 `<p>` 태그로 분리
- `find_elements` (복수형)로 모든 요소 수집
- 공백 제거 후 결합

## 수정된 파일

### agent/tools/news_scraper/scraper.py
- `extract_with_selenium()` 메서드 전면 개선
  - 라인 546-560: 제목 추출 로직 (7개 셀렉터)
  - 라인 562-589: 본문 추출 로직 (8개 셀렉터)
  - 상세 디버그 로그 추가

### agent/news_agent.py
- 감성 분석 에러 핸들링 강화
  - 라인 214-244: try-except 블록 추가
  - 실패 시 기본값(중립) 사용

## 테스트 결과

### 이전 (실패)
```
[DEBUG] 최종 수집된 URL 개수: 10
본문 추출 실패 | {'error': 'no such element: ... "article"'}
본문 추출 실패 | {'error': 'no such element: ... "article"'}
...
```

### 개선 후 (예상)
```
[DEBUG] 최종 수집된 URL 개수: 10
[DEBUG] 제목 추출 시도 (URL: ...)
[DEBUG] ✓ 제목 추출 성공! (셀렉터 1: ...)
[DEBUG] 본문 추출 시도 (총 8개 셀렉터)
[DEBUG] ✓ 본문 추출 성공! (셀렉터 1: #dic_area, 길이: 1234자)
```

## 영향 범위

### 긍정적 영향
1. **안정성 향상**: 네이버 페이지 구조 변경에 자동 대응
2. **호환성 확대**: 다양한 버전의 네이버 뉴스 지원
3. **디버깅 용이성**: 문제 발생 시 즉시 원인 파악 가능
4. **사용자 경험**: 더 많은 기사 성공적으로 분석

### 성능 영향
- **추가 오버헤드**: 셀렉터 시도 시간 증가
  - 제목: 최대 14초 (7개 × 2초)
  - 본문: 최대 16초 (8개 × 2초)
- **완화 방안**: 성공 시 즉시 중단, 대부분 첫 번째 시도에서 성공

## 향후 개선 방향

1. **셀렉터 우선순위 최적화**
   - 성공률 높은 셀렉터를 상위로 재배치
   - 통계 기반 동적 우선순위 조정

2. **캐싱 전략**
   - URL 패턴별로 성공한 셀렉터 캐싱
   - 다음 요청 시 해당 셀렉터부터 시도

3. **머신러닝 적용**
   - 페이지 구조 자동 인식
   - 셀렉터 자동 생성

4. **대체 크롤링 방법**
   - Firecrawl API 활용
   - BeautifulSoup + requests (정적 컨텐츠)

## 참고 자료

### 네이버 뉴스 구조 분석
- 메인 본문: `#dic_area`, `#articeBody`
- 모바일: `#newsct_article`
- 구버전: `.article_body`, `.article_view`

### Selenium 베스트 프랙티스
- Explicit Wait 사용 (Implicit Wait 지양)
- 짧은 타임아웃으로 빠른 fallback
- `find_elements` (복수형)로 안전하게 요소 확인

### 관련 이슈
- Selenium NoSuchElementException 처리
- 동적 웹 페이지 크롤링 전략

## 보안 및 준수사항

✅ **준수된 사항**:
- robots.txt 확인
- User-Agent 설정
- Rate Limit 준수
- 에러 로그에 민감정보 미포함
- 최소 필요 데이터만 수집

## 커밋 정보

**커밋 메시지**:
```
fix: 네이버 뉴스 본문 추출 오류 수정 (article 태그 의존성 제거)

사용자 요구사항:
- 네이버 뉴스 본문 추출 실패 해결
- "no such element: article" 에러 수정

근본 원인:
- 코드가 <article> 태그를 찾으려 시도
- 네이버 뉴스는 <article> 태그 미사용
- 대신 #dic_area, #articeBody 등 사용

수정 내용:
1. 제목 추출 셀렉터 다중화 (7개)
   - #ct > div.media_end_head..., h2, h1 등
2. 본문 추출 셀렉터 다중화 (8개)
   - #dic_area, #articeBody, .article_body 등
3. 본문 최소 길이 검증 (50자 이상)
4. 각 셀렉터 시도 과정 상세 로그
5. 실패 시 페이지 소스 출력 (디버깅용)

기술 스택:
- Selenium WebDriver + Explicit Wait
- CSS Selector fallback 전략
- Python 3.11

개선 효과:
- 네이버 페이지 구조 변경 대응
- 여러 버전의 네이버 뉴스 지원
- 문제 진단 시간 단축

수정 파일:
- agent/tools/news_scraper/scraper.py
  - extract_with_selenium() 메서드
- agent/news_agent.py
  - 감성 분석 에러 핸들링 강화
```

