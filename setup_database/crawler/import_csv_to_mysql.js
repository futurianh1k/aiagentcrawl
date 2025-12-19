#!/usr/bin/env node
'use strict';

// CSV -> MySQL 임포터 (배치 업서트 방식)
//
// 설명:
// - 크롤러가 생성한 CSV 파일을 읽어 `shopping_crawler.products` 테이블로 업서트합니다.
// - 대량 데이터 처리를 위해 배치 단위로 업로드하며, INSERT ... ON DUPLICATE KEY UPDATE를 사용합니다.
// - 스크립트는 필요시 DB와 테이블을 자동으로 생성합니다.
//
// 환경 변수:
// - MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
// - IMPORT_FILE (기본: ./data/naver_shopping_results.csv)
//
// 사용 예:
//   node crawler/import_csv_to_mysql.js --file ./data/results.csv --batch 200
//   또는
//   IMPORT_FILE=./data/results.csv MYSQL_USER=crawler MYSQL_PASSWORD=secret node crawler/import_csv_to_mysql.js

const fs = require('fs');
const path = require('path');
const minimist = require('minimist');
const csv = require('csv-parser');
const mysql = require('mysql2/promise');
require('dotenv').config();

const argv = minimist(process.argv.slice(2), { alias: { f: 'file', b: 'batch' }, default: { batch: 100 } });
const file = argv.file || process.env.IMPORT_FILE || './data/naver_shopping_results.csv';
const batchSize = Number(argv.batch || process.env.BATCH || 100);

const dbHost = process.env.MYSQL_HOST || 'localhost';
const dbPort = process.env.MYSQL_PORT || 3306;
const dbUser = process.env.MYSQL_USER || 'root';
const dbPassword = process.env.MYSQL_PASSWORD || '';
const dbName = process.env.MYSQL_DATABASE || 'shopping_crawler';

async function ensureProductsTable(connection) {
  const ddl = `
CREATE TABLE IF NOT EXISTS products (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  source VARCHAR(100) NOT NULL,
  product_url VARCHAR(1024) NOT NULL,
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
  UNIQUE KEY uk_product_url (product_url)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;`;
  await connection.query(ddl);
}

async function runImport() {
  if (!fs.existsSync(file)) {
    console.error('CSV file not found:', file);
    process.exit(1);
  }

  const conn = await mysql.createConnection({ host: dbHost, port: dbPort, user: dbUser, password: dbPassword, multipleStatements: true });

  // Ensure DB exists
  await conn.query(`CREATE DATABASE IF NOT EXISTS \`${dbName}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`);
  await conn.query(`USE \`${dbName}\``);

  // Ensure table exists
  await ensureProductsTable(conn);

  const rows = [];

  const stream = fs.createReadStream(file).pipe(csv());

  for await (const rec of stream) {
    // Normalize fields based on crawler CSV
    const title = rec.title || '';
    const price_text = rec.price || rec.price_text || '';
    const price = rec.price_number ? Number(rec.price_number) : (price_text ? Number((price_text.replace(/[^0-9.]/g, '')) || null) : null);
    const image_url = rec.image_url || '';
    const product_url = rec.product_url || '';
    const rating = rec.rating || '';
    const review_count = rec.review_count ? Number(rec.review_count) : null;
    const seller = rec.seller || '';
    const availability = rec.availability || '';
    const scraped_at = rec.scraped_at ? new Date(rec.scraped_at) : null;
    const source = rec.source || 'naver_shopping';

    rows.push([source, product_url, title, price_text, price, image_url, rating, review_count, seller, availability, scraped_at]);

    if (rows.length >= batchSize) {
      await upsertBatch(conn, rows.splice(0));
    }
  }

  if (rows.length) {
    await upsertBatch(conn, rows);
  }

  console.log('Import complete.');
  await conn.end();
}

async function upsertBatch(conn, rows) {
  // INSERT ... ON DUPLICATE KEY UPDATE
  const placeholders = rows.map(() => '(?,?,?,?,?,?,?,?,?,?,?)').join(',');
  const sql = `INSERT INTO products (source, product_url, title, price_text, price, image_url, rating, review_count, seller, availability, scraped_at) VALUES ${placeholders}
ON DUPLICATE KEY UPDATE
  title=VALUES(title), price_text=VALUES(price_text), price=VALUES(price), image_url=VALUES(image_url), rating=VALUES(rating), review_count=VALUES(review_count), seller=VALUES(seller), availability=VALUES(availability), scraped_at=VALUES(scraped_at), updated_at=CURRENT_TIMESTAMP`;

  const flat = rows.flat();
  await conn.query(sql, flat);
  console.log(`Imported/updated ${rows.length} rows`);
}

runImport().catch(err => { console.error('Import error:', err); process.exit(1); });
