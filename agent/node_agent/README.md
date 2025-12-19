# Calculator Planner Agent (Node)

Simple node implementation inspired by `lab1`-`lab4` Python exercises.

- Tools: arithmetic, news scraping (dummy), sentiment analysis, trend, summarizer.
- Planner: rule-based decision to call math or news pipeline.
- API: POST /api/plan { query }

Usage:
1. npm install
2. npm start
3. POST to /api/plan with JSON {"query":"3 + 5"} or {"query":"삼성전자 뉴스 여론 분석해줘"}

Notes:
- If you want LLM integration, set `OPENAI_API_KEY` in `.env` and the server will enable an LLM-backed planner automatically.
- Web UI: open http://localhost:3000 after running the server to use the simple UI in `public/`.
- Tests: npm test (uses jest)
