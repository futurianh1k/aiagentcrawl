-- shopping_crawler 데이터베이스 DDL 및 사용 안내
--
-- 설명:
-- 이 파일은 크롤러가 수집한 상품 정보를 저장하기 위한 스키마를 정의합니다.
-- - products: 최종(정규화된) 상품 레코드를 보관 (product_url 기준 유니크)
-- - products_import: CSV 등으로 임시 업로드한 원시 데이터를 검증/가공 후 병합할 때 사용
--
-- 사용 예:
--  1) DB/테이블 생성:
--     mysql -u root -p < create_shopping_tables.sql
--  2) CSV 로드 (예시: products_import 사용):
--     LOAD DATA LOCAL INFILE 'naver_shopping_results.csv' INTO TABLE products_import
--     ... 또는 import_csv_to_mysql.js 스크립트를 사용하여 배치 업서트 권장
--
-- 주의사항:
-- - LOAD DATA LOCAL INFILE는 서버 설정에 따라 제한될 수 있으므로 권한을 확인하세요.
-- - DDL 변경 시 기존 테이블의 데이터 마이그레이션 계획을 세우세요.

-- 1) Create database
CREATE DATABASE IF NOT EXISTS shopping_crawler
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci
  COMMENT 'Shopping crawler data store';

USE shopping_crawler;

-- 2) Main products table (de-duplicated by product_url)
CREATE TABLE IF NOT EXISTS products (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  source VARCHAR(100) NOT NULL COMMENT 'source name e.g. naver_shopping',
  product_url VARCHAR(1024) NOT NULL COMMENT 'canonical product URL',
  title VARCHAR(1024) NOT NULL,
  price_text VARCHAR(100) DEFAULT NULL,
  price DECIMAL(12,2) DEFAULT NULL,
  image_url VARCHAR(2048) DEFAULT NULL,
  rating VARCHAR(50) DEFAULT NULL,
  review_count INT DEFAULT NULL,
  seller VARCHAR(255) DEFAULT NULL,
  availability VARCHAR(50) DEFAULT NULL,
  scraped_at DATETIME DEFAULT NULL,
  inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_product_url (product_url),
  INDEX idx_source (source),
  INDEX idx_price (price),
  INDEX idx_scraped_at (scraped_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3) Staging/import table (useful for CSV bulk loads)
CREATE TABLE IF NOT EXISTS products_import (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  title TEXT,
  price_text VARCHAR(100) DEFAULT NULL,
  price DECIMAL(12,2) DEFAULT NULL,
  image_url VARCHAR(2048) DEFAULT NULL,
  product_url VARCHAR(1024) DEFAULT NULL,
  rating VARCHAR(50) DEFAULT NULL,
  review_count INT DEFAULT NULL,
  seller VARCHAR(255) DEFAULT NULL,
  availability VARCHAR(50) DEFAULT NULL,
  scraped_at DATETIME DEFAULT NULL,
  source VARCHAR(100) DEFAULT NULL,
  raw_csv_line TEXT,
  imported BOOLEAN DEFAULT FALSE,
  import_error TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_product_url (product_url),
  INDEX idx_imported (imported)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4) Example insert from import table into products (dedupe on product_url)
-- Run after loading CSV into products_import
--
-- INSERT INTO products (source, product_url, title, price_text, price, image_url, rating, review_count, seller, availability, scraped_at)
-- SELECT source, product_url, title, price_text, price, image_url, rating, review_count, seller, availability, scraped_at
-- FROM products_import
-- ON DUPLICATE KEY UPDATE
--   title=VALUES(title),
--   price_text=VALUES(price_text),
--   price=VALUES(price),
--   image_url=VALUES(image_url),
--   rating=VALUES(rating),
--   review_count=VALUES(review_count),
--   seller=VALUES(seller),
--   availability=VALUES(availability),
--   scraped_at=VALUES(scraped_at),
--   updated_at=CURRENT_TIMESTAMP;

-- 5) Example LOAD DATA LOCAL INFILE (requires server and client allowing LOCAL INFILE)
-- Change the path to the CSV file (on the machine running the client)
--
-- LOAD DATA LOCAL INFILE 'naver_shopping_results.csv'
-- INTO TABLE products_import
-- FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
-- (title, price, price_number, image_url, product_url, rating, review_count, seller, availability, scraped_at, source);

-- Notes:
-- - Use the staging table for validation before merging into the canonical 'products' table.
-- - Consider adding full-text indexes if you need search by title/content.
-- - Adjust column sizes based on observed data.
