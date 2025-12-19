// robots_check.js
//
// 간단한 robots.txt fetch 및 파서
// - fetchRobotsTxt(origin): robots.txt를 가져옵니다. 실패 시 빈 문자열을 반환합니다.
// - parseRobots(txt, userAgent): robots 파일을 파싱하여 주어진 user-agent에 대한 disallow 목록과 crawl-delay를 반환합니다.
// - checkRobots(origin, userAgent, path): 주어진 origin과 path에 대해 크롤링 허용 여부와 crawl-delay를 확인합니다.
//
// 사용 예시:
//   const { checkRobots } = require('./robots_check');
//   const res = await checkRobots('https://search.shopping.naver.com', '*', '/search/all');
//   if (!res.allowed) { /* 중단 */ }

const https = require('https');
const http = require('http');
const { URL } = require('url');

function fetchRobotsTxt(origin) {
  return new Promise((resolve, reject) => {
    try {
      const url = new URL('/robots.txt', origin).toString();
      const lib = url.startsWith('https:') ? https : http;
      lib.get(url, (res) => {
        let data = '';
        res.setEncoding('utf8');
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          if (res.statusCode >= 400) return resolve('');
          resolve(data);
        });
      }).on('error', (err) => resolve(''));
    } catch (err) {
      resolve('');
    }
  });
}

function parseRobots(txt, userAgent = '*') {
  const lines = txt.split(/\r?\n/).map(l => l.trim());
  let currentAgents = [];
  const rules = {};
  for (const line of lines) {
    if (!line || line.startsWith('#')) continue;
    const m = line.match(/^([^:]+):\s*(.*)$/);
    if (!m) continue;
    const key = m[1].toLowerCase();
    const value = m[2];
    if (key === 'user-agent') {
      currentAgents = [value.toLowerCase()];
      if (!rules[currentAgents[0]]) rules[currentAgents[0]] = { disallow: [], crawlDelay: null };
    } else if (key === 'disallow') {
      for (const ag of currentAgents) rules[ag].disallow.push(value);
    } else if (key === 'crawl-delay') {
      const d = Number(value);
      for (const ag of currentAgents) rules[ag].crawlDelay = isNaN(d) ? null : d;
    }
  }

  // Prefer exact user-agent, then wildcard '*'
  const ua = userAgent.toLowerCase();
  const rule = rules[ua] || rules['*'] || { disallow: [], crawlDelay: null };
  return rule;
}

async function checkRobots(origin, userAgent = '*', path = '/') {
  try {
    const txt = await fetchRobotsTxt(origin);
    if (!txt) return { allowed: true, crawlDelay: null };
    const rule = parseRobots(txt, userAgent);
    // simple path check: if any disallow is prefix of path, it's disallowed
    for (const dis of rule.disallow) {
      if (!dis) continue; // empty disallow means allow all
      if (path.startsWith(dis)) return { allowed: false, crawlDelay: rule.crawlDelay };
    }
    return { allowed: true, crawlDelay: rule.crawlDelay };
  } catch (err) {
    return { allowed: true, crawlDelay: null };
  }
}

module.exports = { checkRobots };
