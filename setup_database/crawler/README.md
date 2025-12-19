# Naver Shopping Crawler (Playwright)

Quick start

1. Install dependencies:

   npm install
   npm run install:playwright

2. Run the crawler:

   node crawler/naver_shopping_crawler.js --query "노트북" --pages 5 --output results.csv --auto-yes

Options

- --query <문자열>  검색어
- --url <URL>        직접 검색/카테고리 URL 사용 (우선순위)
- --pages <n>       스크롤/페이지 반복 횟수 (기본 5)
- --maxItems <n>    최대 수집 항목 수 (기본 200)
- --output <file>   CSV 출력 파일 (기본 naver_shopping_results.csv)
- --delay <ms>      페이지 스크롤 후 대기 시간 (ms)
- --headless        true/false (기본 true)

Notes

- The crawler uses Playwright (Chromium). Some selectors on Naver Shopping may change over time; the script uses a resilient extraction strategy but may need tweaks for future layout changes.
- Respect robots.txt and the site's terms of service — the crawler now supports `--respect-robots` (default true). When robots.txt has a `Crawl-delay` directive, the crawler will use it to increase the delay.
- No login is performed.

Output CSV columns: title, price, price_number, image_url, product_url, rating, review_count, seller, availability, scraped_at, source

Improvements

- Retries and exponential backoff: page navigation and extraction use retries by default (`--maxRetries`, `--backoffBase`).
- Local-file smoke test: `npm run test:smoke` runs a deterministic extraction against a bundled HTML fixture (no external network).
- A GitHub Actions workflow executes the smoke test on push/pull requests to `main` (see `.github/workflows/smoke-test.yml`).

Docker & Import Usage

- Build and run (uses a local MySQL instance via docker-compose):

  docker-compose up --build

  The compose setup will start MySQL and run the crawler container which writes CSV to `./data/results.csv` by default.

- Import CSV into MySQL (after the crawler finishes):

  npm run import:csv

  This runs `crawler/import_csv_to_mysql.js` which reads `./data/naver_shopping_results.csv` (or use `--file` to change) and upserts into the `shopping_crawler.products` table.

- Example: to run a single crawl and import locally:

  # start DB
  docker-compose up -d db
  # run crawler
  node crawler/naver_shopping_crawler.js --query "노트북" --pages 3 --output ./data/naver_shopping_results.csv --auto-yes
  # import
  npm run import:csv

