# 프로젝트 사용자 매뉴얼

🎯 목적 요약

이 프로젝트는 다음을 돕습니다:
- MySQL 기반 뉴스 감정분석 시스템을 위한 데이터베이스 초기화 및 테스트 도구
- 네이버 쇼핑 상품 목록을 크롤링하는 Node.js + Playwright 기반 크롤러
- 크롤링 결과를 CSV로 저장하고, MySQL에 업로드하는 파이프라인
- Docker 및 docker-compose로 환경을 재현 가능하게 포장

이 문서는 전체 워크플로우, 설치/사용 방법, 구성 옵션, 문제 해결 방법을 단계별로 안내합니다.

---

## 목차
1. 전체 워크플로우 개요 ✅
2. 준비물 (Prerequisites) 🧰
3. 빠른 시작 가이드 (로컬) ⚡
4. Docker 기반 실행 (권장 재현성) 🐳
5. 크롤러 상세 사용법 (옵션/예시) 🔧
6. CSV → MySQL 임포트 방법 🗄️
7. 테스트 및 CI (스모크 테스트) ✅
8. 환경 변수 및 설정 목록 🧩
9. 운영 시 주의사항 / 보안 권장사항 ⚠️
10. 문제 해결 가이드 (Troubleshooting) 🛠️
11. 파일/디렉터리 설명 (프로젝트 구조) 📁
12. 다음 단계 권장사항 (옵션) ➕

---

## 1) 전체 워크플로우 개요

1. 로컬/서버에서 크롤러를 실행하여 네이버 쇼핑에서 상품 목록을 수집합니다. (결과: CSV 파일)
2. CSV를 검증/정제 후 `import_csv_to_mysql.js`를 이용하여 MySQL의 `shopping_crawler.products` 테이블로 업서트합니다.
3. 데이터 베이스에서 필요한 쿼리, 알림, ETL, 또는 추가 분석을 수행합니다.
4. (Optional) `04_database_setup.sql`로 뉴스 감정분석 관련 스키마를 초기화하여 본 강의 코드와 연동합니다.

---

## 2) 준비물 (Prerequisites)

- Node.js 18+ 및 npm
- (로컬) Playwright 브라우저 패키지: `npx playwright install --with-deps`
- Docker & docker-compose (Docker 방식으로 실행하려면)
- (CSV → DB) MySQL 8.0 (로컬 또는 컨테이너)
- 권장 패키지: `mysql2`, `dotenv`, `csv-writer`, `csv-parser`, `playwright`

설치 예시:

```bash
# 프로젝트 루트에서
npm install
npx playwright install --with-deps
```

---

## 3) 빠른 시작 가이드 (로컬 실행)

1. 데이터 폴더 준비 (결과 저장용)

```bash
mkdir -p data
```

2. 샘플 크롤링 실행 (검색어: 노트북)

```bash
node crawler/naver_shopping_crawler.js --query "노트북" --pages 3 --output ./data/naver_results.csv --auto-yes
```

옵션 설명:
- `--pages` : 스크롤/페이지 반복 횟수
- `--delay` : 스크롤 후 대기(ms)
- `--maxItems` : 최대 수집 항목 수
- `--output` : 출력 CSV 경로

3. CSV가 생성되면 DB로 업로드:

```bash
# .env를 사용하거나 환경변수로 MYSQL_USER 등 설정
npm run import:csv
# 또는
node crawler/import_csv_to_mysql.js --file ./data/naver_results.csv
```

4. DB에 데이터가 정상적으로 업서트 되었는지 확인합니다 (MySQL client 사용).

---

## 4) Docker 기반 실행 (권장)

Compose 구성은 `docker-compose.yml`에 정의되어 있으며, MySQL과 크롤러 컨테이너를 함께 기동합니다.

```bash
# 빌드와 실행
docker-compose up --build
```

- 기본 동작: 크롤러가 시작되어 `./data/results.csv`에 결과를 씁니다.
- Docker 환경 변수는 `docker-compose.yml`에서 변경하거나 `.env` 파일을 사용해 오버라이드할 수 있습니다.

컨테이너 중지:

```bash
docker-compose down
```

**주의:** 기본 비밀번호는 예시용이므로 프로덕션에서는 즉시 변경하세요.

---

## 5) 크롤러 상세 사용법 & 옵션

기본 명령:

```bash
node crawler/naver_shopping_crawler.js --query "노트북" --pages 5 --delay 1500 --output ./data/out.csv --auto-yes
```

주요 옵션:
- `--query` / `--url` : 검색어 또는 검색결과 URL
- `--localFile` : 로컬 HTML 파일을 사용해 추출(테스트용)
- `--pages` : 스크롤/페이지 반복 횟수
- `--maxItems` : 최대 항목 수
- `--delay` : 스크롤 후 대기(ms). robots.txt의 crawl-delay가 있으면 우선 반영됩니다
- `--respect-robots` : robots.txt 준수 여부 (기본 true)
- `--maxRetries` / `--backoffBase` : 재시도 및 백오프 설정
- `--headless` : true/false

생성되는 CSV 컬럼:
`title, price, price_number, image_url, product_url, rating, review_count, seller, availability, scraped_at, source`

---

## 6) CSV → MySQL 임포트

스크립트: `crawler/import_csv_to_mysql.js`

환경변수 예:

```bash
MYSQL_HOST=localhost MYSQL_PORT=3306 MYSQL_USER=crawler MYSQL_PASSWORD=secret MYSQL_DATABASE=shopping_crawler
node crawler/import_csv_to_mysql.js --file ./data/naver_results.csv --batch 200
```

- 동작: CSV를 파싱하여 배치 단위로 INSERT ... ON DUPLICATE KEY UPDATE 수행 (product_url 유니크키 기준)
- 테이블이 없으면 자동 생성합니다 (`products` 테이블)

---

## 7) 테스트 및 CI (스모크 테스트)

- 로컬 스모크 테스트:

```bash
npm run test:smoke
```

- GitHub Actions:
  - `.github/workflows/smoke-test.yml`에 정의됨 — PR/Push 시 smoke test 실행
  - 스모크 테스트는 네트워크에 의존하지 않고 `crawler/test/fixtures/sample_search.html` 파일을 기반으로 로컬 DOM 추출을 검증합니다.

---

## 8) 환경 변수 & 설정 목록 (요약)

크롤러 (env 또는 CLI):
- `SEARCH_QUERY` / `START_URL` / `LOCAL_FILE`
- `PAGES` (default 5)
- `MAX_ITEMS` (default 200)
- `OUTPUT` (CSV 경로)
- `DELAY` (ms)
- `HEADLESS` (true/false)
- `RESPECT_ROBOTS` (true/false)
- `MAX_RETRIES`, `BACKOFF_BASE` (ms)

임포트/DB:
- `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- `IMPORT_FILE` (csv 경로)

유틸:
- `NODE_ENV`, `CI` 등 일반 Node 환경 변수

---

## 9) 운영 시 주의사항 / 보안 권장사항

- 비밀번호는 환경변수나 시크릿 매니저로 관리하고 코드에 하드코딩하지 마세요.
- DB 접근 권한은 최소 권한 원칙을 따르세요 (크롤러 전용 DB 사용자 권장).
- 크롤링 시 robots.txt 및 사이트 이용 정책을 존중하세요. 높은 빈도/대량 요청은 차단당할 수 있습니다.
- Playwright 베이스 이미지는 브라우저와 시스템 의존성을 포함하므로 이미지 크기가 큽니다. 디스크/네트워크 용량을 고려하세요.

---

## 10) 문제 해결 가이드 (간단)

- 크롤러가 아무것도 저장하지 않을 때:
  - `--query` 또는 `--url` 파라미터가 올바른지 확인
  - `--pages`와 `--delay` 값을 늘려 보세요 (더 많은 스크롤/더 긴 대기)
  - robots.txt가 허용하는지 확인 (`--respect-robots false`로 테스트 가능)

- Playwright 실행 실패 (특히 Docker):
  - `npx playwright install --with-deps`를 실행하여 필요한 브라우저 종속성을 설치하세요.
  - Docker 컨테이너에서 권한/디바이스 제한으로 실패할 수 있으니 `mcr.microsoft.com/playwright` 기반 이미지를 사용하세요.

- CSV 임포트 중 연결 실패:
  - MySQL 자격 증명(MYSQL_USER / PASSWORD)과 호스트(MYSQL_HOST)가 올바른지 확인하세요.
  - MySQL 서버가 `--local-infile` 설정을 필요로 하지 않습니다 (스크립트는 CSV 파싱으로 업서트합니다)

---

## 11) 파일/디렉터리 설명 (주요)

- `04_database_setup.sql` : 뉴스 감정분석 DB 초기화 스크립트
- `05_python_connection_test.py` : Python 기반 연결/테스트 유틸
- `run_sql_file.py`, `run-sql.js` : MySQL에 .sql 파일을 실행하는 유틸 (Python/Node 버전)
- `crawler/` : 크롤러 관련 코드
  - `naver_shopping_crawler.js` : 메인 크롤러
  - `import_csv_to_mysql.js` : CSV → MySQL 업서트 스크립트
  - `sql/create_shopping_tables.sql` : 쇼핑 데이터 저장용 DDL
  - `test/fixtures/` : 스모크 테스트 HTML fixture
- `Dockerfile`, `docker-compose.yml` : 도커 및 컴포즈 설정
- `.github/workflows/smoke-test.yml` : CI 스모크 테스트 워크플로우

---

## 12) 다음 단계 권장사항 (옵션)

- 모니터링/로깅 추가: 크롤러의 성공/실패, 처리량, 에러 유형을 로그로 남기고 알림(예: Slack) 연동
- 스케줄러 통합: 크론 또는 Airflow 등을 이용해 정기 크롤링 자동화
- 데이터 정제/중복 제거 강화: 상품 URL 정규화, 가격 변동 히스토리 수집
- 보안 강화: 비밀값을 Vault에 저장, 이미지를 스캔, 취약점 점검

---

궁금한 점이나 문서 내용에 추가/수정할 부분이 있으면 알려주세요 — 바로 반영하겠습니다. ✨
