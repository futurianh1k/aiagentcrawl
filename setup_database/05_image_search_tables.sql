-- ============================================================================
-- 이미지 검색 시스템 테이블 생성 스크립트
-- 
-- 목적: 이미지 검색 세션 및 결과 저장
-- 생성일: 2025년 12월
-- ============================================================================

USE news_sentiment_analysis;

-- ============================================================================
-- 이미지 검색 세션 테이블
-- ============================================================================

CREATE TABLE IF NOT EXISTS image_search_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '세션 고유 ID',
    query VARCHAR(500) NOT NULL COMMENT '검색 쿼리 (프롬프트)',
    query_type VARCHAR(20) DEFAULT 'text' COMMENT '검색 타입: text, image, mixed',
    search_operator VARCHAR(10) DEFAULT 'AND' COMMENT '검색 연산자: AND, OR',
    status VARCHAR(50) DEFAULT 'pending' COMMENT '상태: pending, processing, completed, failed',
    total_results INT DEFAULT 0 COMMENT '검색 결과 수',
    error_message TEXT COMMENT '오류 메시지 (실패 시)',
    
    -- 샘플 이미지 정보 (이미지 업로드 검색 시)
    sample_image_url VARCHAR(1000) COMMENT '업로드된 샘플 이미지 URL',
    sample_image_path VARCHAR(500) COMMENT '로컬 저장 경로',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    completed_at TIMESTAMP NULL COMMENT '완료 시간',
    
    INDEX idx_query (query),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_query_type (query_type)
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='이미지 검색 세션 테이블';

-- ============================================================================
-- 이미지 검색 결과 테이블
-- ============================================================================

CREATE TABLE IF NOT EXISTS image_search_results (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '결과 고유 ID',
    session_id INT NOT NULL COMMENT '검색 세션 ID',
    
    -- 이미지 URL 및 저장 정보
    image_url VARCHAR(1000) NOT NULL COMMENT '원본 이미지 URL',
    thumbnail_url VARCHAR(1000) COMMENT '썸네일 URL',
    image_path VARCHAR(500) COMMENT '로컬 저장 경로 (선택적)',
    
    -- 이미지 메타데이터
    title VARCHAR(500) COMMENT '이미지 제목 또는 설명',
    source_url VARCHAR(1000) COMMENT '이미지가 있는 페이지 URL',
    source_site VARCHAR(100) COMMENT '출처 사이트 (Google, Naver 등)',
    
    -- 이미지 정보
    width INT COMMENT '이미지 너비 (픽셀)',
    height INT COMMENT '이미지 높이 (픽셀)',
    file_size INT COMMENT '파일 크기 (bytes)',
    mime_type VARCHAR(100) COMMENT 'MIME 타입 (image/jpeg, image/png 등)',
    
    -- 유사도 점수 (샘플 이미지 검색 시)
    similarity_score FLOAT COMMENT '유사도 점수 (0.0 ~ 1.0)',
    
    -- 순서 (검색 결과 순위)
    display_order INT DEFAULT 0 COMMENT '표시 순서',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '생성 시간',
    
    -- 외래키 제약조건
    FOREIGN KEY (session_id) REFERENCES image_search_sessions(id) ON DELETE CASCADE,
    
    -- 인덱스 설정
    INDEX idx_session_id (session_id),
    INDEX idx_display_order (display_order),
    INDEX idx_similarity_score (similarity_score),
    INDEX idx_source_site (source_site)
    
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='이미지 검색 결과 테이블';

-- ============================================================================
-- 테이블 생성 확인
-- ============================================================================

SELECT '✅ 이미지 검색 테이블이 성공적으로 생성되었습니다!' as result;
SELECT TABLE_NAME, TABLE_COMMENT 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'news_sentiment_analysis' 
  AND TABLE_NAME IN ('image_search_sessions', 'image_search_results');
