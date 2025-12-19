# 프로젝트 리뷰 및 리팩토링 계획 2

## 📋 프로젝트 개요

**프로젝트명**: AI Agent 기반 뉴스 감성 분석 시스템  
**목적**: 사용자가 키워드나 문장을 입력하면, 해당 키워드에 대한 뉴스를 크롤링하고 댓글을 분석하고, 시각화하는 시스템

## 🔍 현재 프로젝트 구조 분석

### 현재 폴더 구조
```
aiagent/
├── lab1_basic_agent/          # lab1~lab4 파일들이 모두 여기에 있음
│   ├── lab1_basic_agent.py
│   ├── lab1_basic_agent_working.py
│   ├── lab2_news_scraper.py
│   ├── lab3_data_analyzer.py
│   ├── lab4_planner_agent.py
│   ├── streamlit_app.py
│   ├── streamlit_app_working.py
│   ├── fixedbychatgpt/        # 중복 파일들
│   └── ...
├── lab4_frontend_backend/     # 별도로 분리된 프론트엔드/백엔드
├── lab_session3_agent/        # 세션3 관련 파일들
└── ...
```

### 주요 문제점

1. **구조적 문제**
   - lab1~lab4 파일들이 모두 `lab1_basic_agent` 폴더에 있음
   - 각 lab이 독립적인 폴더로 분리되지 않음
   - 중복 파일들 (`working`, `fixedbychatgpt` 등)이 많음

2. **코드 품질 문제**
   - 공통 모듈이 분리되지 않음
   - 코드 중복이 많음
   - 타입 힌트가 일관되지 않음
   - 에러 처리가 미흡함
   - 보안 가이드라인이 적용되지 않음

3. **의존성 관리**
   - requirements.txt가 중복되어 있음
   - 환경 변수 관리가 일관되지 않음

## 📊 각 Lab별 분석

### Lab 1: Basic Agent (Calculator)
**파일**: `lab1_basic_agent.py`, `lab1_basic_agent_working.py`

**기능**:
- LangChain 기본 Agent 구조 이해
- Calculator Tool 구현
- Streamlit GUI 제공

**문제점**:
- `create_agent` 사용법이 최신 LangChain 버전과 맞지 않을 수 있음
- 에러 처리가 미흡함
- API 키 검증 로직이 약함

### Lab 2: News Scraper
**파일**: `lab2_news_scraper.py`

**기능**:
- Selenium을 이용한 네이버 뉴스 크롤링
- Firecrawl API 연동
- 댓글 추출

**문제점**:
- 하드코딩된 CSS Selector (유지보수 어려움)
- 에러 처리가 미흡함
- 리소스 정리가 제대로 되지 않음
- robots.txt 준수 여부 확인 없음

### Lab 3: Data Analyzer
**파일**: `lab3_data_analyzer.py`

**기능**:
- OpenAI/Gemini를 이용한 감성 분석
- 댓글 단위 및 기사 단위 분석

**문제점**:
- API 키가 로그에 노출될 위험
- JSON 파싱 에러 처리가 미흡함
- Rate Limit 대응 없음
- 개인정보 마스킹 없음

### Lab 4: Planner Agent
**파일**: `lab4_planner_agent.py`

**기능**:
- 여러 Tools를 통합하는 Planner Agent
- 자연어 의도 파악 및 Tool 순차 실행

**문제점**:
- 더미 데이터 사용 (실제 Tool 연동 미흡)
- 에러 처리가 미흡함
- 메모리 관리가 제대로 되지 않음

## 🎯 리팩토링 목표

1. **프로젝트 구조 개선**
   - lab1~lab4를 각각 독립적인 폴더로 분리
   - 공통 모듈을 `common/` 폴더로 추출
   - 중복 파일 정리

2. **코드 품질 개선**
   - 타입 힌트 추가
   - 에러 처리 강화
   - 보안 가이드라인 적용
   - 코드 중복 제거

3. **의존성 관리 개선**
   - 통합 requirements.txt
   - 환경 변수 관리 개선
   - .env.example 제공

## 📁 새로운 프로젝트 구조

```
aiagent/
├── common/                     # 공통 모듈
│   ├── __init__.py
│   ├── config.py              # 설정 관리
│   ├── models.py              # 공통 데이터 모델
│   ├── utils.py               # 유틸리티 함수
│   └── security.py            # 보안 관련 함수
├── lab1_basic_agent/          # Lab 1: Basic Agent
│   ├── __init__.py
│   ├── agent.py               # Calculator Agent
│   ├── tools.py               # Calculator Tools
│   ├── streamlit_app.py       # Streamlit GUI
│   ├── requirements.txt
│   └── README.md
├── lab2_news_scraper/         # Lab 2: News Scraper
│   ├── __init__.py
│   ├── scraper.py             # News Scraper Tool
│   ├── models.py              # NewsArticle 모델
│   ├── requirements.txt
│   └── README.md
├── lab3_data_analyzer/        # Lab 3: Data Analyzer
│   ├── __init__.py
│   ├── analyzer.py            # Data Analyzer Tool
│   ├── models.py              # SentimentResult 모델
│   ├── requirements.txt
│   └── README.md
├── lab4_planner_agent/        # Lab 4: Planner Agent
│   ├── __init__.py
│   ├── planner.py             # Planner Agent
│   ├── requirements.txt
│   └── README.md
├── lab4_frontend_backend/     # Lab 4: Frontend/Backend (기존 유지)
├── requirements.txt           # 통합 requirements
├── .env.example               # 환경 변수 템플릿
├── README.md                  # 프로젝트 전체 README
└── PROJECT_REVIEW.md          # 이 문서
```

## 🔒 보안 개선 사항

1. **API 키 관리**
   - 환경 변수에서만 읽기
   - 로그에 절대 노출하지 않음
   - .env 파일을 .gitignore에 추가

2. **입력 검증**
   - 모든 사용자 입력 검증
   - SQL Injection 방지
   - XSS 방지

3. **에러 처리**
   - 민감한 정보를 에러 메시지에 포함하지 않음
   - 일반화된 에러 메시지 제공

4. **크롤링**
   - robots.txt 준수
   - Rate Limit 준수
   - User-Agent 설정

## 📝 다음 단계

1. ✅ 프로젝트 리뷰 문서 작성
2. ⏳ 폴더 구조 재구성
3. ⏳ 공통 모듈 추출
4. ⏳ 각 Lab 코드 리팩토링
5. ⏳ 보안 가이드라인 적용
6. ⏳ 테스트 코드 작성
7. ⏳ 문서화 업데이트

## 📚 참고 자료

- LangChain 공식 문서: https://docs.langchain.com/
- OpenAI API 문서: https://platform.openai.com/docs/
- Selenium 문서: https://selenium-python.readthedocs.io/
- 보안 코딩 가이드라인: 프로젝트 내 A01.review.md 참조

