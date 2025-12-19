/*
Planner: simple rule-based planner that decides which tools to call.
If OpenAI key is present and OpenAI client available, planner can call out to LLM (optional).
*/

import { add, multiply, divide, scrapeNews, analyzeTrend, summarizeResults } from './tools.js';
import { analyzeSentiment } from './tools.js';
import dotenv from 'dotenv';
dotenv.config();

const OPENAI_API_KEY = process.env.OPENAI_API_KEY || null;

export class Planner {
  constructor() {
  }

  // detect arithmetic queries (numbers and operators)
  isMathQuery(q) {
    return /[0-9]+\s*[+\-*\/\%\(\)]/.test(q);
  }

  // detect news analysis queries
  isNewsQuery(q) {
    return /뉴스|여론|댓글|감성|분석|요약/.test(q);
  }

  async planAndExecute(q, opts={}) {
    q = (q||'').trim();
    if (!q) return '질의를 입력하세요.';

    if (this.isMathQuery(q)) {
      try {
        // extract numbers and operators to form expression
        const expr = q.replace(/[^0-9+\-*/().%]/g, '');
        // eslint-disable-next-line no-eval
        const value = eval(expr);
        return String(value);
      } catch (e) {
        return `수식 처리 실패: ${e.message}`;
      }
    }

    if (this.isNewsQuery(q)) {
      const keywordMatch = q.match(/(?:about|에 대한|에 대해|관련).*?(\w+)/i);
      const keyword = keywordMatch ? keywordMatch[1] : (q.split(' ')[0] || '대상');
      const news = scrapeNews(keyword, 3);
      const trend = analyzeTrend(news, keyword);
      const summary = summarizeResults(trend);
      return { news, trend, summary, planner: 'rule' };
    }

    // default answer
    return "지원하지 않는 질의 유형입니다. (수식 또는 뉴스 분석을 시도해보세요)";
  }
}

export default Planner;