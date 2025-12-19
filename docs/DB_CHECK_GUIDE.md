# 데이터베이스 크롤링 기록 확인 가이드

## 빠른 참조

### MySQL 컨테이너 접속
```bash
# MySQL 컨테이너에 접속
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment

# 또는 root로 접속
docker-compose exec mysql mysql -u root -prootpassword123 news_sentiment
```

### 기본 쿼리
```sql
-- 분석 세션 목록 확인
SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT 10;

-- 특정 세션의 기사 확인
SELECT * FROM articles WHERE session_id = 1;

-- 댓글 확인
SELECT * FROM comments WHERE article_id = 1;
```

---

## 방법 1: MySQL 컨테이너 직접 접속

### 1. MySQL 컨테이너 접속

```bash
# 일반 사용자로 접속
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment

# Root 사용자로 접속
docker-compose exec mysql mysql -u root -prootpassword123 news_sentiment
```

### 2. 데이터베이스 및 테이블 확인

```sql
-- 데이터베이스 목록 확인
SHOW DATABASES;

-- 현재 데이터베이스 사용
USE news_sentiment;

-- 테이블 목록 확인
SHOW TABLES;

-- 테이블 구조 확인
DESCRIBE analysis_sessions;
DESCRIBE articles;
DESCRIBE comments;
DESCRIBE keywords;
```

### 3. 크롤링 기록 조회

#### 분석 세션 목록
```sql
-- 최근 분석 세션 10개
SELECT 
    id,
    keyword,
    sources,
    status,
    created_at,
    completed_at
FROM analysis_sessions 
ORDER BY created_at DESC 
LIMIT 10;
```

#### 특정 세션의 상세 정보
```sql
-- 세션 ID 1의 정보
SELECT * FROM analysis_sessions WHERE id = 1;

-- 세션의 기사 수
SELECT COUNT(*) as article_count 
FROM articles 
WHERE session_id = 1;

-- 세션의 댓글 수
SELECT COUNT(*) as comment_count 
FROM comments c
JOIN articles a ON c.article_id = a.id
WHERE a.session_id = 1;
```

#### 기사 목록
```sql
-- 특정 세션의 모든 기사
SELECT 
    id,
    title,
    source,
    sentiment_label,
    sentiment_score,
    confidence,
    published_at
FROM articles 
WHERE session_id = 1
ORDER BY published_at DESC;
```

#### 댓글 목록
```sql
-- 특정 기사의 댓글
SELECT 
    id,
    content,
    author,
    sentiment_label,
    sentiment_score,
    confidence,
    created_at
FROM comments 
WHERE article_id = 1
ORDER BY created_at DESC;
```

#### 키워드 목록
```sql
-- 특정 세션의 키워드
SELECT 
    keyword,
    frequency,
    sentiment_score
FROM keywords 
WHERE session_id = 1
ORDER BY frequency DESC;
```

### 4. 통계 조회

```sql
-- 전체 통계
SELECT 
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_sessions,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_sessions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_sessions
FROM analysis_sessions;

-- 세션별 기사 수
SELECT 
    s.id,
    s.keyword,
    s.status,
    COUNT(a.id) as article_count
FROM analysis_sessions s
LEFT JOIN articles a ON s.id = a.session_id
GROUP BY s.id, s.keyword, s.status
ORDER BY s.created_at DESC;

-- 감정 분포
SELECT 
    sentiment_label,
    COUNT(*) as count
FROM articles
GROUP BY sentiment_label;
```

---

## 방법 2: Docker 명령어로 직접 쿼리 실행

### 한 줄로 쿼리 실행

```bash
# 분석 세션 목록 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT * FROM analysis_sessions ORDER BY created_at DESC LIMIT 5;"

# 기사 수 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT COUNT(*) as total_articles FROM articles;"

# 댓글 수 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT COUNT(*) as total_comments FROM comments;"
```

### PowerShell에서 포맷팅

```powershell
# 분석 세션 목록 (표 형식)
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT id, keyword, status, created_at FROM analysis_sessions ORDER BY created_at DESC LIMIT 10;" | Format-Table

# 감정 분포 확인
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT sentiment_label, COUNT(*) as count FROM articles GROUP BY sentiment_label;" | Format-Table
```

---

## 방법 3: Backend API를 통한 확인

### API 엔드포인트 사용

```bash
# 분석 상태 조회
curl http://localhost:8000/api/agents/status/1

# 또는 PowerShell
Invoke-RestMethod -Uri "http://localhost:8000/api/agents/status/1" -Method Get
```

---

## 방법 4: SQL 파일로 저장 후 확인

### 쿼리 결과를 파일로 저장

```bash
# 분석 세션 전체 내보내기
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT * FROM analysis_sessions;" > sessions.csv

# 기사 데이터 내보내기
docker-compose exec mysql mysql -u newsuser -pnewspass123 news_sentiment -e "SELECT * FROM articles;" > articles.csv
```

---

## 유용한 조합 쿼리

### 최근 분석 결과 요약

```sql
SELECT 
    s.id as session_id,
    s.keyword,
    s.status,
    s.created_at,
    COUNT(DISTINCT a.id) as article_count,
    COUNT(DISTINCT c.id) as comment_count,
    AVG(a.sentiment_score) as avg_sentiment
FROM analysis_sessions s
LEFT JOIN articles a ON s.id = a.session_id
LEFT JOIN comments c ON a.id = c.article_id
GROUP BY s.id, s.keyword, s.status, s.created_at
ORDER BY s.created_at DESC
LIMIT 10;
```

### 키워드별 통계

```sql
SELECT 
    keyword,
    COUNT(*) as session_count,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
FROM analysis_sessions
GROUP BY keyword
ORDER BY session_count DESC;
```

### 감정 분석 결과 요약

```sql
SELECT 
    a.session_id,
    s.keyword,
    a.sentiment_label,
    COUNT(*) as count,
    AVG(a.confidence) as avg_confidence
FROM articles a
JOIN analysis_sessions s ON a.session_id = s.id
GROUP BY a.session_id, s.keyword, a.sentiment_label
ORDER BY a.session_id DESC, count DESC;
```

---

## 문제 해결

### 데이터베이스 연결 확인

```bash
# MySQL 컨테이너 상태 확인
docker-compose ps mysql

# MySQL 로그 확인
docker-compose logs mysql

# MySQL 컨테이너 내부 접속 테스트
docker-compose exec mysql mysqladmin -u root -prootpassword123 ping
```

### 테이블이 없는 경우

```bash
# 데이터베이스 초기화 스크립트 확인
cat setup_database/04_database_setup.sql

# 수동으로 테이블 생성 (필요시)
docker-compose exec mysql mysql -u root -prootpassword123 news_sentiment < setup_database/04_database_setup.sql
```

---

## 데이터 삭제 (주의!)

### 특정 세션 삭제

```sql
-- 세션과 관련된 모든 데이터 삭제
DELETE FROM comments WHERE article_id IN (SELECT id FROM articles WHERE session_id = 1);
DELETE FROM keywords WHERE session_id = 1;
DELETE FROM articles WHERE session_id = 1;
DELETE FROM analysis_sessions WHERE id = 1;
```

### 모든 데이터 삭제 (초기화)

```sql
-- 모든 데이터 삭제 (주의!)
DELETE FROM comments;
DELETE FROM keywords;
DELETE FROM articles;
DELETE FROM analysis_sessions;
```

---

## 참고사항

1. **데이터베이스 정보**:
   - 데이터베이스명: `news_sentiment`
   - 사용자: `newsuser` / 비밀번호: `newspass123`
   - Root 비밀번호: `rootpassword123`

2. **주요 테이블**:
   - `analysis_sessions`: 분석 세션 정보
   - `articles`: 크롤링된 기사
   - `comments`: 기사 댓글
   - `keywords`: 추출된 키워드

3. **보안**: 프로덕션 환경에서는 비밀번호를 환경 변수로 관리하세요.

