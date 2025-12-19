-- ============================================================================
-- MySQL 데이터베이스 초기화 스크립트
-- 
-- 목적: 2회차 강의 - AI 에이전트 기반 뉴스 감정분석 시스템
-- 생성일: 2024년
-- 
-- 이 스크립트는 다음을 수행합니다:
-- 1. 데이터베이스 생성 (UTF8MB4 인코딩)
-- 2. 전용 사용자 계정 생성 및 권한 부여
-- 3. 뉴스 감정분석 시스템용 테이블 생성
-- 4. 인덱스 최적화 및 뷰 생성
-- 5. 초기 설정 데이터 삽입
-- ============================================================================

-- 현재 연결 정보 확인
SELECT CONCAT('현재 접속 사용자: ', USER()) AS connection_info;
SELECT CONCAT('MySQL 버전: ', VERSION()) AS version_info;

-- ============================================================================
-- 1. 데이터베이스 생성
-- ============================================================================

-- 데이터베이스가 존재하면 삭제 (개발환경에서만 사용)
-- DROP DATABASE IF EXISTS news_sentiment_analysis;

-- UTF8MB4 문자셋으로 데이터베이스 생성 (다국어 지원)
CREATE DATABASE IF NOT EXISTS news_sentiment_analysis
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci
    COMMENT '뉴스 감정분석 시스템 데이터베이스';

-- 데이터베이스 생성 확인
SHOW CREATE DATABASE news_sentiment_analysis;

-- ============================================================================
-- 2. 사용자 계정 생성 및 권한 설정
-- ============================================================================

-- 기존 사용자 제거 (존재하는 경우)
DROP USER IF EXISTS 'news_app'@'localhost';

-- 뉴스 앱 전용 사용자 생성
CREATE USER 'news_app'@'localhost' 
    IDENTIFIED BY 'secure_password_here'
    COMMENT '뉴스 감정분석 시스템 전용 사용자';

-- 데이터베이스 권한 부여
GRANT ALL PRIVILEGES ON news_sentiment_analysis.* TO 'news_app'@'localhost';

-- 권한 새로고침
FLUSH PRIVILEGES;

-- 사용자 생성 확인
SELECT User, Host, plugin, authentication_string != '' as has_password 
FROM mysql.user 
WHERE User = 'news_app';

-- ============================================================================
-- 3. 데이터베이스 선택 및 테이블 생성
-- ============================================================================

USE news_sentiment_analysis;

-- 현재 데이터베이스 확인
SELECT DATABASE() as current_database;

-- ============================================================================
-- 3.1 크롤링 세션 테이블
-- ============================================================================

CREATE TABLE IF NOT EXISTS crawl_sessions (
    session_id VARCHAR(50) PRIMARY KEY COMMENT '크롤링 세션 고유 ID',
    start_time DATETIME NOT NULL COMMENT '크롤링 시작 시간',
    end_time DATETIME NULL COMMENT '크롤링 종료 시간',
    status ENUM('started', 'completed', 'failed', 'cancelled') DEFAULT 'started' COMMENT '세션 상태',
    target_keywords JSON COMMENT '크롤링 대상 키워드 목록',
    articles_collected INT DEFAULT 0 COMMENT '수집된 기사 수',
    comments_collected INT DEFAULT 0 COMMENT '수집된 댓글 수',
    error_message TEXT COMMENT '오류 메시지 (실패 시)',
    config_snapshot JSON COMMENT '크롤링 설정 스냅샷',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시간',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '마지막 업데이트 시간',

    INDEX idx_session_start_time (start_time),
    INDEX idx_session_status (status),
    INDEX idx_session_created (created_at)

) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='크롤링 세션 관리 테이블';

-- ============================================================================
-- 3.2 뉴스 기사 테이블 (메인 테이블)
-- ============================================================================

CREATE TABLE IF NOT EXISTS articles (
    article_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '기사 고유 ID',
    session_id VARCHAR(50) NULL COMMENT '수집 세션 ID',
    url VARCHAR(512) UNIQUE NOT NULL COMMENT '기사 URL (고유)',
    title VARCHAR(255) NOT NULL COMMENT '기사 제목',
    content TEXT COMMENT '기사 본문',
    summary TEXT COMMENT '기사 요약 (자동 생성)',
    source VARCHAR(100) NOT NULL COMMENT '출처 (네이버, 다음 등)',
    category VARCHAR(50) COMMENT '카테고리 (정치, 경제 등)',
    author VARCHAR(100) COMMENT '기자명',
    published_at DATETIME COMMENT '기사 발행일시',
    view_count INT DEFAULT 0 COMMENT '조회수',
    like_count INT DEFAULT 0 COMMENT '좋아요 수',
    comment_count INT DEFAULT 0 COMMENT '댓글 수 (캐시)',

    -- 감정분석 결과
    overall_sentiment VARCHAR(20) COMMENT '전체 감정 (positive/negative/neutral)',
    sentiment_confidence FLOAT COMMENT '감정분석 신뢰도 (0.0-1.0)',
    emotion_scores JSON COMMENT '세부 감정 점수 (기쁨, 분노, 슬픔 등)',

    -- 메타데이터
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시간',
    processed_at DATETIME COMMENT '감정분석 처리 시간',
    last_updated DATETIME COMMENT '마지막 업데이트 시간',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시간',

    -- 외래키 제약조건
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(session_id) ON DELETE SET NULL,

    -- 인덱스 설정 (성능 최적화)
    INDEX idx_url (url),
    INDEX idx_source (source),
    INDEX idx_category (category),
    INDEX idx_published_at (published_at),
    INDEX idx_crawled_at (crawled_at),
    INDEX idx_overall_sentiment (overall_sentiment),
    INDEX idx_source_published (source, published_at),
    INDEX idx_active_published (is_active, published_at),

    -- 전문 검색 인덱스 (제목, 내용)
    FULLTEXT INDEX ft_title (title),
    FULLTEXT INDEX ft_content (content),
    FULLTEXT INDEX ft_title_content (title, content)

) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='뉴스 기사 정보 테이블';

-- ============================================================================
-- 3.3 댓글 테이블
-- ============================================================================

CREATE TABLE IF NOT EXISTS comments (
    comment_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '댓글 고유 ID',
    article_id INT NOT NULL COMMENT '연관 기사 ID',
    session_id VARCHAR(50) NULL COMMENT '수집 세션 ID',

    -- 댓글 기본 정보
    text TEXT NOT NULL COMMENT '댓글 내용',
    author VARCHAR(100) COMMENT '작성자 (닉네임)',
    author_id VARCHAR(100) COMMENT '작성자 ID (해시화됨)',
    written_at DATETIME COMMENT '댓글 작성일시',
    like_count INT DEFAULT 0 COMMENT '좋아요 수',
    reply_count INT DEFAULT 0 COMMENT '답글 수',

    -- 계층 구조 (답글 지원)
    parent_comment_id INT NULL COMMENT '부모 댓글 ID (답글인 경우)',
    depth TINYINT DEFAULT 0 COMMENT '댓글 깊이 (0:원댓글, 1:답글)',

    -- 감정분석 결과
    sentiment VARCHAR(20) COMMENT '감정 (positive/negative/neutral)',
    sentiment_confidence FLOAT COMMENT '감정분석 신뢰도',
    emotion_scores JSON COMMENT '세부 감정 점수',
    toxicity_score FLOAT COMMENT '독성 댓글 점수 (0.0-1.0)',

    -- 메타데이터
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '크롤링 시간',
    processed_at DATETIME COMMENT '감정분석 처리 시간',
    is_filtered BOOLEAN DEFAULT FALSE COMMENT '필터링 여부 (욕설, 스팸)',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '레코드 생성 시간',

    -- 외래키 제약조건
    FOREIGN KEY (article_id) REFERENCES articles(article_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES crawl_sessions(session_id) ON DELETE SET NULL,
    FOREIGN KEY (parent_comment_id) REFERENCES comments(comment_id) ON DELETE CASCADE,

    -- 인덱스 설정
    INDEX idx_article_id (article_id),
    INDEX idx_author (author),
    INDEX idx_written_at (written_at),
    INDEX idx_sentiment (sentiment),
    INDEX idx_parent_comment (parent_comment_id),
    INDEX idx_article_sentiment (article_id, sentiment),
    INDEX idx_article_written (article_id, written_at),

    -- 전문 검색 인덱스
    FULLTEXT INDEX ft_comment_text (text)

) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='뉴스 댓글 정보 테이블';

-- ============================================================================
-- 3.4 키워드 테이블
-- ============================================================================

CREATE TABLE IF NOT EXISTS keywords (
    keyword_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '키워드 고유 ID',
    keyword VARCHAR(100) UNIQUE NOT NULL COMMENT '키워드',
    category VARCHAR(50) COMMENT '키워드 카테고리',
    description TEXT COMMENT '키워드 설명',

    -- 통계 정보
    search_count INT DEFAULT 0 COMMENT '검색된 횟수',
    article_count INT DEFAULT 0 COMMENT '연관 기사 수',
    last_searched_at DATETIME COMMENT '마지막 검색 시간',

    -- 감정 경향
    avg_sentiment_score FLOAT COMMENT '평균 감정 점수',
    positive_ratio FLOAT COMMENT '긍정 비율',
    negative_ratio FLOAT COMMENT '부정 비율',
    neutral_ratio FLOAT COMMENT '중립 비율',

    -- 메타데이터
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '업데이트 시간',

    -- 인덱스
    INDEX idx_keyword (keyword),
    INDEX idx_category (category),
    INDEX idx_search_count (search_count),
    INDEX idx_active (is_active),

    -- 전문 검색
    FULLTEXT INDEX ft_keyword_desc (keyword, description)

) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='검색 키워드 관리 테이블';

-- ============================================================================
-- 3.5 기사-키워드 연관 테이블 (다대다 관계)
-- ============================================================================

CREATE TABLE IF NOT EXISTS article_keywords (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '연관 관계 ID',
    article_id INT NOT NULL COMMENT '기사 ID',
    keyword_id INT NOT NULL COMMENT '키워드 ID',
    relevance_score FLOAT DEFAULT 1.0 COMMENT '연관도 점수 (0.0-1.0)',
    match_type ENUM('title', 'content', 'tag', 'auto') DEFAULT 'auto' COMMENT '매칭 방식',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '연관 생성 시간',

    -- 외래키 제약조건
    FOREIGN KEY (article_id) REFERENCES articles(article_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,

    -- 중복 방지 (기사-키워드 조합 유니크)
    UNIQUE KEY uk_article_keyword (article_id, keyword_id),

    -- 인덱스
    INDEX idx_article_relevance (article_id, relevance_score),
    INDEX idx_keyword_relevance (keyword_id, relevance_score)

) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='기사-키워드 연관관계 테이블';

-- ============================================================================
-- 4. 뷰 생성 (자주 사용하는 조회 패턴)
-- ============================================================================

-- 4.1 기사 통계 뷰
CREATE OR REPLACE VIEW v_article_stats AS
SELECT 
    a.article_id,
    a.title,
    a.source,
    a.published_at,
    a.overall_sentiment,
    a.sentiment_confidence,
    COUNT(c.comment_id) as actual_comment_count,
    AVG(c.sentiment_confidence) as avg_comment_sentiment_confidence,
    SUM(CASE WHEN c.sentiment = 'positive' THEN 1 ELSE 0 END) as positive_comments,
    SUM(CASE WHEN c.sentiment = 'negative' THEN 1 ELSE 0 END) as negative_comments,
    SUM(CASE WHEN c.sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_comments
FROM articles a
LEFT JOIN comments c ON a.article_id = c.article_id
WHERE a.is_active = TRUE
GROUP BY a.article_id, a.title, a.source, a.published_at, a.overall_sentiment, a.sentiment_confidence;

-- 4.2 키워드 인기도 뷰
CREATE OR REPLACE VIEW v_keyword_popularity AS
SELECT 
    k.keyword_id,
    k.keyword,
    k.category,
    k.search_count,
    COUNT(ak.article_id) as linked_articles,
    AVG(ak.relevance_score) as avg_relevance,
    MAX(a.published_at) as latest_article_date,
    k.last_searched_at
FROM keywords k
LEFT JOIN article_keywords ak ON k.keyword_id = ak.keyword_id
LEFT JOIN articles a ON ak.article_id = a.article_id
WHERE k.is_active = TRUE
GROUP BY k.keyword_id, k.keyword, k.category, k.search_count, k.last_searched_at
ORDER BY k.search_count DESC, linked_articles DESC;

-- 4.3 일별 감정 트렌드 뷰
CREATE OR REPLACE VIEW v_daily_sentiment_trend AS
SELECT 
    DATE(published_at) as date,
    source,
    COUNT(*) as total_articles,
    SUM(CASE WHEN overall_sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
    SUM(CASE WHEN overall_sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
    SUM(CASE WHEN overall_sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
    AVG(sentiment_confidence) as avg_confidence
FROM articles 
WHERE published_at IS NOT NULL 
  AND is_active = TRUE
  AND published_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(published_at), source
ORDER BY date DESC, source;

-- ============================================================================
-- 5. 초기 데이터 삽입
-- ============================================================================

-- 5.1 기본 키워드 삽입
INSERT IGNORE INTO keywords (keyword, category, description, is_active) VALUES
('인공지능', 'technology', 'AI, 머신러닝 관련 뉴스', TRUE),
('경제', 'economy', '경제 전반 관련 뉴스', TRUE),
('정치', 'politics', '정치 관련 뉴스', TRUE),
('사회', 'society', '사회 이슈 관련 뉴스', TRUE),
('스포츠', 'sports', '스포츠 관련 뉴스', TRUE),
('문화', 'culture', '문화, 예술 관련 뉴스', TRUE),
('기술', 'technology', '과학기술 관련 뉴스', TRUE),
('환경', 'environment', '환경, 기후 관련 뉴스', TRUE),
('건강', 'health', '보건, 의료 관련 뉴스', TRUE),
('교육', 'education', '교육 관련 뉴스', TRUE);

-- 5.2 테스트용 크롤링 세션 삽입
INSERT IGNORE INTO crawl_sessions (
    session_id, 
    start_time, 
    end_time, 
    status, 
    target_keywords, 
    articles_collected,
    comments_collected,
    config_snapshot
) VALUES (
    'test_session_001',
    NOW() - INTERVAL 1 HOUR,
    NOW() - INTERVAL 30 MINUTE,
    'completed',
    JSON_ARRAY('인공지능', '기술'),
    0,
    0,
    JSON_OBJECT('max_articles', 100, 'include_comments', true, 'sentiment_analysis', true)
);

-- ============================================================================
-- 6. 데이터베이스 설정 최적화
-- ============================================================================

-- 6.1 테이블 통계 업데이트
ANALYZE TABLE crawl_sessions, articles, comments, keywords, article_keywords;

-- 6.2 현재 테이블 목록 및 상태 확인
SHOW TABLE STATUS FROM news_sentiment_analysis;

-- ============================================================================
-- 7. 설치 확인 쿼리
-- ============================================================================

-- 7.1 생성된 테이블 확인
SELECT 
    TABLE_NAME as '테이블명',
    TABLE_ROWS as '레코드수',
    CREATE_TIME as '생성시간',
    TABLE_COMMENT as '설명'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'news_sentiment_analysis'
ORDER BY TABLE_NAME;

-- 7.2 생성된 뷰 확인
SELECT 
    TABLE_NAME as '뷰명',
    VIEW_DEFINITION as '뷰정의'
FROM information_schema.VIEWS 
WHERE TABLE_SCHEMA = 'news_sentiment_analysis';

-- 7.3 인덱스 확인
SELECT 
    TABLE_NAME as '테이블명',
    INDEX_NAME as '인덱스명',
    COLUMN_NAME as '컬럼명',
    INDEX_TYPE as '인덱스타입'
FROM information_schema.STATISTICS 
WHERE TABLE_SCHEMA = 'news_sentiment_analysis'
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- 7.4 사용자 권한 확인
SHOW GRANTS FOR 'news_app'@'localhost';

-- ============================================================================
-- 8. 성공 메시지
-- ============================================================================

SELECT '✅ MySQL 데이터베이스 초기화가 성공적으로 완료되었습니다!' as result;
SELECT CONCAT('📊 생성된 테이블: ', COUNT(*), '개') as table_count
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'news_sentiment_analysis';

-- ============================================================================
-- 스크립트 종료
-- ============================================================================
