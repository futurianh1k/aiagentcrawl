/*
Tools: add, multiply, divide, scrapeNews (dummy), analyzeSentiment (simple), analyzeTrend, summarizeResults
These are pure JS functions. They are written to be synchronous and testable.
*/

export function add(x, y) {
  return x + y;
}

export function multiply(x, y) {
  return x * y;
}

export function divide(x, y) {
  if (y === 0) throw new Error('Division by zero');
  return x / y;
}

export function scrapeNews(keyword, maxArticles = 3) {
  // Dummy data similar to Python labs
  return {
    keyword,
    articles: [
      {
        title: `${keyword} 관련 주요 뉴스 1`,
        url: 'https://news.example.com/1',
        content: `${keyword}에 대한 긍정적인 전망이 제시되었습니다.`,
        comments: [
          { text: '좋은 소식이네요!', author: 'user1' },
          { text: '기대됩니다.', author: 'user2' },
          { text: '신중하게 지켜봐야겠어요.', author: 'user3' }
        ]
      },
      {
        title: `${keyword} 관련 주요 뉴스 2`,
        url: 'https://news.example.com/2',
        content: `${keyword}에 대한 우려의 목소리도 나오고 있습니다.`,
        comments: [
          { text: '걱정이 됩니다.', author: 'user4' },
          { text: '더 신중해야 할 것 같아요.', author: 'user5' },
          { text: '장단점을 모두 고려해야죠.', author: 'user6' }
        ]
      }
    ],
    total_articles: 2,
    total_comments: 6
  };
}

export function analyzeSentiment(text) {
  const positive = ['좋', '훌륭', '기대', '찬성', '지지', '만족'];
  const negative = ['나쁘', '걱정', '우려', '반대', '실망', '문제', '위험'];
  const txt = text.toLowerCase();
  let pos = 0;
  let neg = 0;
  positive.forEach(w => { if (txt.includes(w)) pos++; });
  negative.forEach(w => { if (txt.includes(w)) neg++; });
  let sentiment = '중립';
  let confidence = 0.5;
  if (pos > neg) {
    sentiment = '긍정';
    confidence = Math.min(0.9, 0.6 + pos * 0.1);
  } else if (neg > pos) {
    sentiment = '부정';
    confidence = Math.min(0.9, 0.6 + neg * 0.1);
  }
  return { text, sentiment, confidence };
}

export function analyzeTrend(newsData, keyword) {
  const allComments = [];
  (newsData.articles || []).forEach(a => (a.comments || []).forEach(c => allComments.push(c.text)));
  if (!allComments.length) return { error: '댓글 없음', keyword };
  const counts = { 긍정: 0, 부정: 0, 중립: 0 };
  allComments.forEach(t => {
    const r = analyzeSentiment(t);
    counts[r.sentiment]++;
  });
  const total = counts.긍정 + counts.부정 + counts.중립;
  const dist = Object.fromEntries(Object.entries(counts).map(([k,v])=>[k, v / total]));
  return {
    keyword,
    overall_sentiment: Object.keys(dist).reduce((a,b)=> dist[a]>dist[b]?a:b),
    sentiment_distribution: dist,
    key_topics: [keyword],
    summary: `${keyword}에 대한 여론은 ${Object.keys(dist).reduce((a,b)=> dist[a]>dist[b]?a:b)}적입니다.`,
    total_comments: total
  };
}

export function summarizeResults(trend) {
  if (trend.error) return `❌ 분석 실패: ${trend.error}`;
  const p = (v)=> Number((v*100).toFixed(1))+'%';
  const dist = trend.sentiment_distribution || {};
  return `"${trend.keyword}" 결과: 전체 ${trend.overall_sentiment}, 긍정 ${p(dist.긍정||0)}, 부정 ${p(dist.부정||0)}, 중립 ${p(dist.중립||0)}.`;
}
