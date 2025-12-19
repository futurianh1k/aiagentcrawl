import Planner from '../src/planner.js';

test('math query', async () => {
  const p = new Planner();
  expect(await p.planAndExecute('3 + 5')).toBe('8');
  expect(await p.planAndExecute('((2 + 3) * 4) / 2')).toBe('10');
});

test('news query', async () => {
  const p = new Planner();
  const res = await p.planAndExecute('삼성전자 뉴스 여론 분석해줘');
  expect(res.news).toBeDefined();
  expect(res.trend).toBeDefined();
});
