const qEl = document.getElementById('query');
const outEl = document.getElementById('out');
const submitBtn = document.getElementById('submit');
const clearBtn = document.getElementById('clear');

submitBtn.addEventListener('click', async () => {
  const query = qEl.value.trim();
  if (!query) return;
  outEl.textContent = '처리 중...';
  try {
    const res = await fetch('/api/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || 'Unknown error');
    outEl.textContent = JSON.stringify(data.result, null, 2);
  } catch (e) {
    outEl.textContent = '오류: ' + e.message;
  }
});

clearBtn.addEventListener('click', () => {
  qEl.value = '';
  outEl.textContent = '(결과가 여기에 표시됩니다)';
});