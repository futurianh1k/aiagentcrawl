import OpenAI from 'openai';
import { scrapeNews, analyzeTrend, summarizeResults } from './tools.js';

export class LLMPlanner {
  constructor(apiKey) {
    if (!apiKey) throw new Error('OPENAI_API_KEY is required for LLMPlanner');
    this.client = new OpenAI({ apiKey });
    this.model = 'gpt-4o-mini';
  }

  async classify(query) {
    const prompt = `다음 질의가 수학 계산인지 뉴스 감성 분석(뉴스/댓글)인지 분류하고, 필요한 경우 핵심 키워드 또는 수식을 JSON 형태로 반환하세요.\n\n질의:\n"""${query}"""\n\nJSON 형식 예시:\n{ "type": "math", "expr": "(2+3)*4" }\n또는\n{ "type": "news", "keyword": "삼성전자" }`;

    const res = await this.client.chat.completions.create({
      model: this.model,
      messages: [{ role: 'user', content: prompt }],
      max_tokens: 200,
    });

    const text = res.choices?.[0]?.message?.content || '';
    // Try to extract JSON from the model output
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      try {
        const parsed = JSON.parse(jsonMatch[0]);
        return parsed;
      } catch (e) {
        // fallthrough
      }
    }

    // Fallback: simple heuristics
    if (/[0-9]/.test(query) && /[+\-*/]/.test(query)) {
      return { type: 'math', expr: query.replace(/[^0-9+\-*/().% ]/g, '') };
    }
    return { type: 'news', keyword: query.split(' ')[0] };
  }

  async planAndExecute(query) {
    const decision = await this.classify(query);
    if (decision.type === 'math' && decision.expr) {
      try {
        // eslint-disable-next-line no-eval
        const value = eval(decision.expr);
        return String(value);
      } catch (e) {
        return `수식 처리 실패(LLM 플래너): ${e.message}`;
      }
    }

    if (decision.type === 'news') {
      const keyword = decision.keyword || query.split(' ')[0] || '대상';
      const news = scrapeNews(keyword, 3);
      const trend = analyzeTrend(news, keyword);
      const summary = summarizeResults(trend);
      return { news, trend, summary, planner: 'llm' };
    }

    return "LLM 플래너: 이해하지 못한 질의입니다.";
  }
}

export default LLMPlanner;