#!/usr/bin/env node
'use strict';

// Naver 쇼핑 크롤러 (Playwright 사용)
//
// 요약:
// - 네이버 쇼핑의 검색/카테고리 페이지를 탐색하여 상품 목록을 추출하고 CSV로 저장합니다.
// - Playwright(Chromium)를 사용하여 자바스크립트로 렌더링되는 페이지도 처리합니다.
//
// 주요 기능 및 옵션:
// - 입력: --query (검색어) 또는 --url (직접 검색/카테고리 URL) 또는 --localFile (테스트용 HTML 파일)
// - 출력: CSV (기본: naver_shopping_results.csv) / 환경변수 OUTPUT으로 변경 가능
// - 페이징/무한스크롤: --pages, 스크롤 후 --delay(ms)로 항목 로딩 대기
// - robots.txt 존중: --respect-robots (기본 true) — robots의 Crawl-delay를 반영합니다
// - 재시도/백오프: --maxRetries, --backoffBase (ms)
// - 테스트 모드: --localFile 로 로컬 HTML을 파싱해 추출로직을 검증할 수 있음
//
// 수집 필드 (CSV 컬럼): title, price, price_number, image_url, product_url, rating, review_count, seller, availability, scraped_at, source
//
// 윤리적/법적 유의사항:
// - 대량 크롤링 전에 반드시 대상 사이트의 robots.txt 및 이용약관을 확인하세요.
// - 본 스크립트는 로그인/스크래핑 우회 기능을 제공하지 않습니다.


const fs = require('fs');
const path = require('path');
const minimist = require('minimist');
const createCsvWriter = require('csv-writer').createObjectCsvWriter;
const { chromium } = require('playwright');
require('dotenv').config();
const { checkRobots } = require('./robots_check');

const argv = minimist(process.argv.slice(2), {
  alias: { q: 'query', u: 'url', p: 'pages', o: 'output', d: 'delay' },
  default: { pages: 5, output: 'naver_shopping_results.csv', delay: 1500, headless: true, maxItems: 200, respectRobots: true, maxRetries: 3, backoffBase: 1000 }
});

// Allow configuration via CLI or environment variables
const query = argv.query || process.env.SEARCH_QUERY || null;
const startUrl = argv.url || process.env.START_URL || null;
let pages = Number(argv.pages || process.env.PAGES || 5);
let maxItems = Number(argv.maxItems || process.env.MAX_ITEMS || 200);
let outFile = argv.output || process.env.OUTPUT || 'naver_shopping_results.csv';
let delay = Number(argv.delay || process.env.DELAY || 1500);
const headless = (typeof argv.headless !== 'undefined') ? argv.headless : (process.env.HEADLESS ? process.env.HEADLESS.toLowerCase() !== 'false' : true);
const respectRobots = (typeof argv.respectRobots !== 'undefined') ? !!argv.respectRobots : (typeof process.env.RESPECT_ROBOTS !== 'undefined' ? process.env.RESPECT_ROBOTS.toLowerCase() !== 'false' : true);
const maxRetries = Number(argv.maxRetries || process.env.MAX_RETRIES || 3);
const backoffBase = Number(argv.backoffBase || process.env.BACKOFF_BASE || 1000);
const localFile = argv.localFile || process.env.LOCAL_FILE || null;

if (!query && !startUrl && !localFile) {
  console.error('Error: Provide --query "검색어" or --url "검색/카테고리 URL" or set SEARCH_QUERY/START_URL or specify --localFile');
  process.exit(1);
}

// If localFile mode is used, we will set page content from file instead of navigating
if (localFile && !fs.existsSync(localFile)) {
  console.error('Local file not found:', localFile);
  process.exit(1);
}
    { id: 'title', title: 'title' },
    { id: 'price', title: 'price' },
    { id: 'price_number', title: 'price_number' },
    { id: 'image_url', title: 'image_url' },
    { id: 'product_url', title: 'product_url' },
    { id: 'rating', title: 'rating' },
    { id: 'review_count', title: 'review_count' },
    { id: 'seller', title: 'seller' },
    { id: 'availability', title: 'availability' },
    { id: 'scraped_at', title: 'scraped_at' },
    { id: 'source', title: 'source' }
  ],
  append: false
});

// Helper: retry function with exponential backoff
async function retryWithBackoff(fn, attempts = 3, baseDelay = 1000) {
  let lastErr;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      const delay = baseDelay * Math.pow(2, i);
      console.warn(`Attempt ${i + 1}/${attempts} failed: ${err.message || err}. Retrying in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw lastErr;
}


function normalizePrice(priceText) {
  if (!priceText) return '';
  const digits = priceText.replace(/[^0-9]/g, '');
  return digits ? Number(digits) : '';
}

function parseIntSafe(text) {
  if (!text) return '';
  const m = text.replace(/[^0-9]/g, '');
  return m ? Number(m) : '';
}

async function extractFromPage(page) {
  /*
    추출 전략(요약):
    - 페이지 내 모든 <a> 엘리먼트를 후보로 삼고, href에 'product' 또는 'catalog', 'shopping.naver.com' 같은
      패턴이 있는 링크를 우선 필터합니다.
    - 각 링크에서 가장 가까운 리스트 항목(li) 또는 div 컨테이너를 찾아 제목, 가격, 이미지 등 필요한 필드를 추출합니다.
    - 사이트 구조가 언제든 바뀔 수 있으므로 다수의 선택자와 폴백을 사용하여 실패율을 낮춥니다.

    참고: 이 함수는 페이지 컨텍스트에서 실행되므로 DOM 접근 코드를 포함합니다.
  */
  return await page.evaluate(() => {
    const results = [];
    // Candidate anchors that likely link to a product page
    const anchors = Array.from(document.querySelectorAll('a')).filter(a => {
      const href = a.href || '';
      // product or catalog links in Naver Shopping often include 'product' or 'catalog' paths
      return /product|catalog|shopping.naver.com/.test(href) && (a.innerText || a.querySelector('img'));
    });

    const seen = new Set();

    for (const a of anchors) {
      const url = a.href.split('#')[0];
      if (!url || seen.has(url) || url.startsWith('javascript:')) continue;
      seen.add(url);

      const container = a.closest('li') || a.closest('div');
      const title = (a.innerText && a.innerText.trim()) || (container && (container.querySelector('a')?.innerText || container.querySelector('img')?.alt)) || '';

      let priceText = '';
      if (container) {
        const priceEl = container.querySelector('[class*=price], [class*=Price], strong, span');
        if (priceEl) priceText = priceEl.innerText || '';
      }

      // fallback: find nearby price using sibling elements
      if (!priceText) {
        const nearPrice = document.querySelectorAll('em');
        for (let el of nearPrice) {
          if (/\d+[,.]?\d*/.test(el.innerText || '')) { priceText = el.innerText; break; }
        }
      }

      const imgEl = container?.querySelector('img') || a.querySelector('img');
      const image = imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || '') : '';

      // rating and review
      const ratingEl = container?.querySelector('[class*=rating], [class*=score], .rating') || null;
      const ratingText = ratingEl ? ratingEl.innerText : '';

      const reviewEl = container?.querySelector('[class*=review], [class*=count], .count') || null;
      const reviewText = reviewEl ? reviewEl.innerText : '';

      const sellerEl = container?.querySelector('[class*=mall], [class*=seller], .mall') || null;
      const seller = sellerEl ? sellerEl.innerText : '';

      const availability = /품절|절판|sold out|soldout/i.test(container?.innerText || '') ? 'out of stock' : 'in stock';

      results.push({ title: title.trim(), priceText: (priceText || '').trim(), image, url, ratingText: (ratingText || '').trim(), reviewText: (reviewText || '').trim(), seller: (seller || '').trim(), availability });
    }

    return results;
  });
}

async function run() {
  console.log('Starting crawler (Naver Shopping)');
  const browser = await chromium.launch({ headless });
  const context = await browser.newContext({ userAgent: 'Mozilla/5.0 (compatible; crawler/1.0; +https://example.com/bot)' });
  const page = await context.newPage();

  let url = startUrl;
  if (!url && query) {
    const q = encodeURIComponent(query);
    url = `https://search.shopping.naver.com/search/all?query=${q}`;
  }

  console.log('Opening:', url);

  // robots.txt check
  try {
    if (respectRobots) {
      const origin = new URL(url).origin;
      const p = new URL(url).pathname || '/';
      const robots = await checkRobots(origin, '*', p);
      if (!robots.allowed) {
        console.error('Robots.txt disallows crawling this path. Aborting.');
        await browser.close();
        process.exit(2);
      }
      if (robots.crawlDelay) {
        const crawlMs = Math.max(delay, robots.crawlDelay * 1000);
        console.log(`Robots.txt crawl-delay found: ${robots.crawlDelay}s — setting delay=${crawlMs}ms`);
        delay = crawlMs;
      }
    }
  } catch (err) {
    console.warn('Robots.txt check failed, continuing:', err.message || err);
  }

  // Navigate with retries
  await retryWithBackoff(() => page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 }), maxRetries, backoffBase);

  const scraped = [];
  const seenUrls = new Set();

  for (let i = 0; i < pages; i++) {
    console.log(`Page/scroll iteration ${i + 1}/${pages} — scrolling and waiting ${delay}ms`);

    // Scroll down to load more items
    await page.evaluate(() => {
      window.scrollBy(0, window.innerHeight * 2);
    });

    await page.waitForTimeout(delay);

    // Extract current items (with retries)
    try {
      const items = await retryWithBackoff(() => extractFromPage(page), maxRetries, backoffBase);
      console.log(`  Found ${items.length} candidate items on page`);
      for (const it of items) {
        if (!it.url) continue;
        if (seenUrls.has(it.url)) continue;
        seenUrls.add(it.url);
        // normalize price and numbers
        const priceNumber = (it.priceText && it.priceText.replace(/[^0-9]/g, '')) ? Number(it.priceText.replace(/[^0-9]/g, '')) : '';
        const review_count = (it.reviewText && it.reviewText.replace(/[^0-9]/g, '')) ? Number(it.reviewText.replace(/[^0-9]/g, '')) : '';
        scraped.push({
          title: it.title || '',
          price: it.priceText || '',
          price_number: priceNumber,
          image_url: it.image || '',
          product_url: it.url,
          rating: it.ratingText || '',
          review_count: review_count,
          seller: it.seller || '',
          availability: it.availability || '',
          scraped_at: new Date().toISOString(),
          source: 'naver_shopping'
        });
        if (scraped.length >= maxItems) break;
      }
    } catch (err) {
      console.warn('Error extracting items on iteration', i + 1, err.message || err);
    }

    if (scraped.length >= maxItems) {
      console.log('Reached maxItems:', maxItems);
      break;
    }

    // attempt to move to next page via query param 'pagingIndex' if present in URL
    // else keep scrolling to load more
    const nextPageUrl = await page.evaluate(() => {
      // try to find paging link
      const a = document.querySelector('a[aria-label="다음"]') || document.querySelector('a.btn_next');
      return a ? a.href : null;
    });
    if (nextPageUrl) {
      try {
        console.log('Navigating to next page via paging link');
        await retryWithBackoff(() => page.goto(nextPageUrl, { waitUntil: 'domcontentloaded' }), maxRetries, backoffBase);
      } catch (e) {
        console.warn('Failed to navigate to next page link:', e.message || e);
      }
    }
  }

  // Deduplicate by URL (already done) and write CSV
  console.log(`Scraped total ${scraped.length} unique items. Writing to ${outFile}`);
  try {
    await csvWriter.writeRecords(scraped);
    console.log('CSV saved:', outFile);
  } catch (e) {
    console.error('Failed to save CSV:', e.message || e);
  }

  await browser.close();
  console.log('Done.');
}

run().catch(err => {
  console.error('Crawler error:', err);
  process.exit(1);
});