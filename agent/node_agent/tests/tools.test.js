import { add, multiply, divide, scrapeNews, analyzeSentiment, analyzeTrend, summarizeResults } from '../src/tools.js';

test('add/multiply/divide', () => {
  expect(add(2,3)).toBe(5);
  expect(multiply(4,5)).toBe(20);
  expect(divide(10,2)).toBe(5);
  expect(() => divide(1,0)).toThrow();
});

test('news pipeline', () => {
  const news = scrapeNews('테스트');
  expect(news.keyword).toBe('테스트');
  const trend = analyzeTrend(news, '테스트');
  expect(trend.total_comments).toBeGreaterThan(0);
  const summary = summarizeResults(trend);
  expect(typeof summary).toBe('string');
});
