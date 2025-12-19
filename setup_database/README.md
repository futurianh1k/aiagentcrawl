# MySQL 완전 설치 및 설정 가이드

> **2회차 강의: AI 에이전트 기반 뉴스 감정분석 시스템**을 위한 MySQL 개발환경 구축 가이드

## 📋 개요

이 가이드는 MySQL 초보자를 위한 완전한 설치 및 설정 매뉴얼입니다. 
2회차 강의에서 제공하는 뉴스 감정분석 시스템 코드를 실행하기 위한 모든 환경을 준비할 수 있습니다.

## 🖥️ 지원 운영체제

| 운영체제 | 가이드 파일 | 권장 버전 |
|---------|-------------|-----------|
| 🪟 **Windows** | [01_windows_setup.md](./01_windows_setup.md) | Windows 10/11 |
| 🍎 **Mac** | [02_mac_setup.md](./02_mac_setup.md) | macOS 11+ (Intel/Apple Silicon) |
| 🐧 **Ubuntu** | [03_ubuntu_setup.md](./03_ubuntu_setup.md) | Ubuntu 20.04/22.04 LTS |

## ⚡ 빠른 시작

### 1단계: 운영체제별 MySQL 설치
위 표에서 해당하는 운영체제 가이드를 따라 MySQL을 설치하세요.

### 2단계: 데이터베이스 초기화
```bash
# Linux/Mac
chmod +x setup_database.sh
./setup_database.sh

# Windows
setup_database.bat
```

### 3단계: Python 연결 테스트
```bash
python 05_python_connection_test.py
```

## 🗄️ 데이터베이스 구조

이 가이드를 통해 생성되는 데이터베이스는 다음과 같은 구조를 가집니다:

### 📊 **news_sentiment_analysis** 데이터베이스

| 테이블명 | 설명 | 주요 필드 |
|----------|------|-----------|
| **articles** | 뉴스 기사 정보 | url, title, content, source, published_at |
| **comments** | 기사 댓글 | text, author, sentiment, confidence |
| **keywords** | 검색 키워드 | keyword, search_count |
| **crawl_sessions** | 크롤링 세션 기록 | session_id, start_time, end_time, status |

### 🔐 사용자 계정

- **데이터베이스명**: `news_sentiment_analysis`
- **사용자명**: `news_app`
- **기본 비밀번호**: `secure_password_here` (설치 시 변경 권장)
- **권한**: 해당 데이터베이스에 대한 모든 권한

## 🐍 Python 패키지 요구사항

2회차 강의 코드 실행을 위해 다음 패키지가 필요합니다:

```bash
pip install mysql-connector-python sqlalchemy pymysql pandas requests beautifulsoup4 selenium webdriver-manager textblob transformers
```

## 🔧 주요 설정 파일

| 파일명 | 용도 | 설명 |
|--------|------|------|
| `04_database_setup.sql` | 데이터베이스 초기화 | 테이블 생성 및 사용자 권한 설정 |
| `05_python_connection_test.py` | 연결 테스트 | MySQL 및 Python 연결 확인 |
| `setup_database.sh` | 자동 설치 (Linux/Mac) | 원클릭 데이터베이스 설정 |
| `setup_database.bat` | 자동 설치 (Windows) | 원클릭 데이터베이스 설정 |

## 📱 연결 정보 템플릿

### Python 코드에서 사용할 연결 설정:

```python
# mysql-connector-python 사용
import mysql.connector

config = {
    'user': 'news_app',
    'password': 'your_password_here',
    'host': 'localhost',
    'database': 'news_sentiment_analysis',
    'raise_on_warnings': True,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

connection = mysql.connector.connect(**config)
```

```python
# SQLAlchemy 사용 (2회차 강의 코드)
from sqlalchemy import create_engine

DATABASE_URL = "mysql+pymysql://news_app:your_password_here@localhost/news_sentiment_analysis"
engine = create_engine(DATABASE_URL, echo=True)
```

## ✅ 설치 완료 확인

모든 설정이 완료되면 다음 명령어로 확인하세요:

```bash
python 05_python_connection_test.py
```

**성공 시 출력 예시:**
```
✓ mysql-connector-python 패키지 설치 확인
✓ MySQL 서버 연결 성공: news_app@localhost/news_sentiment_analysis
✓ MySQL 버전: 8.0.35
✓ 데이터베이스 테이블 수: 4
✓ SQLAlchemy 패키지 설치 확인
✓ SQLAlchemy 연결 성공
✓ 테이블 조회 성공: 4개

🎉 모든 테스트를 통과했습니다!
2회차 강의 코드를 실행할 준비가 완료되었습니다.
```

## 🚨 문제 해결

문제가 발생하면 [troubleshooting.md](./troubleshooting.md)를 참고하세요.

### 주요 문제 유형:
- ❌ **연결 거부**: MySQL 서비스가 실행되지 않음
- ❌ **인증 실패**: 사용자명/비밀번호 불일치
- ❌ **포트 충돌**: 3306 포트가 다른 프로그램에서 사용 중
- ❌ **문자 인코딩**: UTF8MB4 설정 누락

## 📚 추가 자료

- [MySQL 공식 문서](https://dev.mysql.com/doc/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [Python MySQL 연결 가이드](https://mysql-connector-python.readthedocs.io/)

---

**📧 문의사항**  
설치 과정에서 문제가 발생하면 troubleshooting.md를 먼저 확인하고, 해결되지 않는 경우 강의 Q&A를 이용해 주세요.

**🔄 업데이트**  
이 가이드는 지속적으로 업데이트됩니다. 최신 버전은 강의 자료실에서 확인하세요.
