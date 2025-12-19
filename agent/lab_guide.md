AI 에이전트 기반 뉴스 감성 분석 시스템
1회차 실습 가이드

과정명: AI 에이전트 개념 및 아키텍처 설계
시간: 2시간 (120분)
난이도: 대학원/실무 중급
생성일: 2024년 12월
 
목차
1. 환경 설정 가이드	..................................................	3
2. 실습 1: LangChain 기본 Agent	..................................................	4
3. 실습 2: NewsScraper Tool 구현	..................................................	8
4. 실습 3: DataAnalyzer Tool 구현	..................................................	12
5. 실습 4: Planner Agent 구현	..................................................	16
6. 트러블슈팅 가이드	..................................................	20
7. 추가 학습 자료	..................................................	21
 
1. 환경 설정 가이드
1.1 필수 라이브러리 설치
다음 명령어를 순서대로 실행하여 필요한 라이브러리를 설치하세요:
# 기본 라이브러리
pip install langchain openai python-dotenv

# 웹 크롤링 관련
pip install selenium webdriver-manager requests beautifulsoup4

# AI/ML 관련
pip install google-generativeai

# 데이터베이스 관련
pip install mysql-connector-python sqlalchemy

# 문서 처리 관련
pip install python-docx
1.2 환경 변수 설정
.env 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:
# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API 키 (선택사항)
GEMINI_API_KEY=your_gemini_api_key_here

# Firecrawl API 키 (선택사항)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
1.3 주의사항
• OpenAI API 키는 https://platform.openai.com/api-keys 에서 발급받을 수 있습니다.
• Chrome 브라우저가 설치되어 있어야 Selenium이 정상 작동합니다.
• webdriver-manager가 자동으로 ChromeDriver를 관리하므로 별도 설치가 불필요합니다.
• 실습 중 API 사용량과 비용을 확인하시기 바랍니다.
 
2. 실습 2: LangChain 기본 Agent
2.1 학습 목표
• LangChain의 기본 Agent 구조 이해
• Tool 정의 및 Agent 초기화 방법 학습
• @tool 데코레이터 사용법 습득
• Agent 실행 및 디버깅 방법 이해
2.2 핵심 개념
• @tool 데코레이터로 함수를 Tool로 변환
• initialize_agent로 Agent와 Tools 연결
• AgentType.CONVERSATIONAL_REACT_DESCRIPTION 사용
• ConversationBufferMemory로 대화 기록 관리
• verbose=True로 Agent 사고 과정 관찰
2.3 실습 파일
파일명: lab1_basic_agent.py
위치: 강의 자료 폴더 또는 AI Drive에서 다운로드
2.4 실행 방법
1. lab1_basic_agent.py 파일을 프로젝트 폴더에 저장
2. 터미널에서 다음 명령어 실행:
   python lab1_basic_agent.py
3. 실행 결과 확인 및 코드 분석
 
3. 실습 3: NewsScraper Tool 구현
3.1 학습 목표
• Selenium을 이용한 안정적인 웹 크롤링 구현
• Explicit Wait을 통한 Flaky Test 방지
• Firecrawl MCP를 활용한 구조화된 데이터 추출
• Tool로 패키징하여 Agent에서 사용 가능하도록 구현
3.2 핵심 개념
• Selenium WebDriver 설정 및 Explicit Wait 사용
• CSS Selector를 이용한 안정적인 요소 선택
• Firecrawl API를 통한 구조화된 데이터 추출
• Fallback 메커니즘 (Firecrawl 실패 시 Selenium 사용)
• @tool 데코레이터로 Agent에서 사용 가능한 Tool로 변환
3.3 실습 파일
파일명: lab2_news_scraper.py
위치: 강의 자료 폴더 또는 AI Drive에서 다운로드
3.4 실행 방법
1. lab2_news_scraper.py 파일을 프로젝트 폴더에 저장
2. 터미널에서 다음 명령어 실행:
   python lab2_news_scraper.py
3. 실행 결과 확인 및 코드 분석
 
4. 실습 4: DataAnalyzer Tool 구현
4.1 학습 목표
• OpenAI GPT 또는 Google Gemini를 이용한 감성 분석 구현
• 프롬프트 엔지니어링을 통한 일관된 JSON 응답 확보
• 댓글 단위 및 기사 단위 분석 기능 구현
• Tool로 패키징하여 Agent에서 사용 가능하도록 구현
4.2 핵심 개념
• 프롬프트 엔지니어링으로 일관된 JSON 응답 확보
• OpenAI와 Gemini API의 차이점 및 선택 방법
• JSON 파싱 및 예외 처리로 안정적인 데이터 추출
• 감성 분석과 동향 분석의 구분 및 활용
• @tool 데코레이터로 Agent에서 사용 가능한 Tool로 변환
4.3 실습 파일
파일명: lab3_data_analyzer.py
위치: 강의 자료 폴더 또는 AI Drive에서 다운로드
4.4 실행 방법
1. lab3_data_analyzer.py 파일을 프로젝트 폴더에 저장
2. 터미널에서 다음 명령어 실행:
   python lab3_data_analyzer.py
3. 실행 결과 확인 및 코드 분석
 
5. 실습 5: Planner Agent 구현
5.1 학습 목표
• 여러 Tools를 통합하는 Planner Agent 구현
• 자연어 의도 파악 및 Tool 순차 실행
• 사용자 질의에 따른 동적 Tool 선택
• 전체 End-to-End 파이프라인 구축
5.2 핵심 개념
• 여러 Tools를 하나의 Agent에 통합 등록
• 사용자 질의에 따른 동적 Tool 선택 및 실행
• ConversationBufferMemory로 대화 컨텍스트 유지
• Tool 간 데이터 전달 및 파이프라인 구축
• Agent의 ReAct 패턴 (Reason + Act) 관찰
5.3 실습 파일
파일명: lab4_planner_agent.py
위치: 강의 자료 폴더 또는 AI Drive에서 다운로드
5.4 실행 방법
1. lab4_planner_agent.py 파일을 프로젝트 폴더에 저장
2. 터미널에서 다음 명령어 실행:
   python lab4_planner_agent.py
3. 실행 결과 확인 및 코드 분석
 
6. 트러블슈팅 가이드
6.1 일반적인 오류 및 해결책
• 문제: ImportError: No module named 'langchain'
  해결책: pip install langchain 명령어로 라이브러리를 설치하세요.

• 문제: OpenAI API 키 오류
  해결책: .env 파일에 올바른 API 키가 설정되어 있는지 확인하세요.

• 문제: ChromeDriver 오류
  해결책: Chrome 브라우저를 최신 버전으로 업데이트하고 webdriver-manager를 재설치하세요.

• 문제: Selenium 타임아웃 오류
  해결책: Explicit Wait 시간을 늘리거나 네트워크 연결을 확인하세요.

• 문제: JSON 파싱 오류
  해결책: API 응답 형식을 확인하고 예외 처리 로직을 점검하세요.

6.2 성능 최적화 팁
• Selenium WebDriver는 headless 모드로 실행하여 성능을 향상시키세요.
• API 호출 시 적절한 Rate Limit을 설정하여 제한을 피하세요.
• 대용량 데이터 처리 시 배치 처리를 활용하세요.
• 메모리 사용량을 모니터링하고 필요 시 가비지 컬렉션을 수행하세요.
 
7. 추가 학습 자료
7.1 공식 문서
• LangChain 공식 문서: https://docs.langchain.com/
• LangGraph 공식 문서: https://langchain-ai.github.io/langgraph/
• OpenAI API 문서: https://platform.openai.com/docs/
• Selenium 공식 문서: https://selenium-python.readthedocs.io/
• Google Generative AI 문서: https://ai.google.dev/docs/
7.2 온라인 강의 및 튜토리얼
• DeepLearning.AI - LangChain for LLM Application Development
• LangChain Academy (무료 온라인 코스)
• YouTube - LangChain 튜토리얼 시리즈
• Coursera - AI Agents 전문 과정
• Udemy - Selenium WebDriver 완전 정복
7.3 실습 프로젝트 아이디어
• 주식 시장 뉴스 감성 분석 및 투자 인사이트 제공 시스템
• 소셜 미디어 트렌드 분석 및 마케팅 인사이트 도구
• 고객 리뷰 자동 분석 및 제품 개선 제안 시스템
• 뉴스 기사 자동 요약 및 키워드 추출 도구
• 다국어 댓글 번역 및 감성 분석 플랫폼
7.4 커뮤니티 및 지원
• LangChain Discord 커뮤니티
• GitHub Discussions - LangChain 저장소
• Stack Overflow - langchain 태그
• Reddit - r/MachineLearning 커뮤니티
• 국내 AI 개발자 커뮤니티 및 밋업
