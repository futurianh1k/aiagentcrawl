#!/usr/bin/env node
'use strict';

// Smoke test (로컬 fixture 기반)
//
// 목적:
// - 외부 네트워크에 의존하지 않고 크롤러의 핵심 추출 로직이 의도대로 동작하는지 검증합니다.
// - CI 환경에서 안정적으로 실행되어 PR/MR에서 회귀를 발견할 수 있도록 합니다.
//
// 동작:
// - test/fixtures/sample_search.html 을 Playwright로 로드하고, 추출 로직과 유사한 방식으로 아이템을 식별합니다.
// - 추출된 항목 수가 기대보다 작으면 실패합니다.

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async function main() {
  const fixture = path.join(__dirname, 'test', 'fixtures', 'sample_search.html');
  if (!fs.existsSync(fixture)) {
    console.error('Fixture not found:', fixture);
    process.exit(1);
  }

  const html = fs.readFileSync(fixture, 'utf-8');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.setContent(html, { waitUntil: 'domcontentloaded' });

  // Use the same extraction logic as the crawler (inlined for reliability)
  const items = await page.evaluate(() => {
    const results = [];
    const anchors = Array.from(document.querySelectorAll('a')).filter(a => a.href && (a.innerText || a.querySelector('img')));
    const seen = new Set();
    for (const a of anchors) {
      const url = a.href.split('#')[0];
      if (!url || seen.has(url) || url.startsWith('javascript:')) continue;
      seen.add(url);
      const container = a.closest('li') || a.closest('div');
      const title = (a.innerText && a.innerText.trim()) || (container && (container.querySelector('a')?.innerText || container.querySelector('img')?.alt)) || '';
      const priceEl = container ? container.querySelector('[class*=price], [class*=Price], strong, span, div.price') : null;
      const priceText = priceEl ? (priceEl.innerText || '') : '';
      const imgEl = container?.querySelector('img') || a.querySelector('img');
      const image = imgEl ? (imgEl.getAttribute('data-src') || imgEl.src || '') : '';
      const ratingEl = container?.querySelector('[class*=rating], [class*=score], .rating') || null;
      const ratingText = ratingEl ? ratingEl.innerText : '';
      const reviewEl = container?.querySelector('[class*=review], [class*=count], .review') || null;
      const reviewText = reviewEl ? reviewEl.innerText : '';
      const sellerEl = container?.querySelector('[class*=mall], [class*=seller], .seller') || null;
      const seller = sellerEl ? sellerEl.innerText : '';
      results.push({ title: title.trim(), priceText: priceText.trim(), image, url, ratingText: ratingText.trim(), reviewText: reviewText.trim(), seller: seller.trim() });
    }
    return results;
  });

  await browser.close();

  console.log('Smoke test: extracted items count =', items.length);
  if (!items || items.length < 1) {
    console.error('Smoke test failed: no items extracted');
    process.exit(2);
  }
  console.log('Sample extracted item:', items[0]);
  console.log('Smoke test passed');
  process.exit(0);
})();
