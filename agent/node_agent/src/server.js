import express from 'express';
import bodyParser from 'body-parser';
import Planner from './planner.js';
import LLMPlanner from './llm_planner.js';
import dotenv from 'dotenv';

dotenv.config();
const OPENAI_API_KEY = process.env.OPENAI_API_KEY || null;
const app = express();
app.use(bodyParser.json());

let planner;
try {
  if (OPENAI_API_KEY) {
    planner = new LLMPlanner(OPENAI_API_KEY);
    console.log('LLMPlanner enabled (using OpenAI)');
  } else {
    planner = new Planner();
    console.log('Rule-based Planner enabled');
  }
} catch (e) {
  console.warn('Failed to initialize LLMPlanner, falling back to rule planner:', e.message);
  planner = new Planner();
}

// Serve static UI from ./public
app.use(express.static(new URL('../public', import.meta.url).pathname));
app.get('/', (req, res) => res.sendFile(new URL('../public/index.html', import.meta.url).pathname));

app.post('/api/plan', async (req, res) => {
  const { query } = req.body;
  try {
    const out = await planner.planAndExecute(query);
    res.json({ ok: true, result: out });
  } catch (e) {
    res.status(500).json({ ok: false, error: String(e) });
  }
});

app.listen(process.env.PORT || 3000, () => {
  console.log('Server listening on port', process.env.PORT || 3000);
});
