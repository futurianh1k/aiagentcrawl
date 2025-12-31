-- 토큰 사용량 필드 추가 (이미 존재하면 무시)
ALTER TABLE analysis_sessions 
ADD COLUMN IF NOT EXISTS prompt_tokens INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS completion_tokens INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS total_tokens INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS estimated_cost FLOAT DEFAULT 0.0;
