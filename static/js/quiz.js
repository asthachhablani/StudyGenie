/* quiz.js */
let currentQuiz = null;
let selectedAnswers = {};

document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();
  const generateForm = document.getElementById('quiz-gen-form');
  const quizArea = document.getElementById('quiz-area');
  const resultArea = document.getElementById('result-area');

  await populateSubjectSelect(document.getElementById('gen-subject'));

  if (generateForm) {
    generateForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Generating...';
      selectedAnswers = {};
      quizArea.innerHTML = '';
      resultArea.innerHTML = '';
      resultArea.classList.add('hidden');

      const payload = {
        subject_id: document.getElementById('gen-subject').value,
        topic: document.getElementById('gen-topic').value.trim(),
        count: parseInt(document.getElementById('gen-count').value) || 10,
        difficulty: document.getElementById('gen-difficulty').value,
      };

      showLoading('Generating quiz...');
      const { ok, data } = await api('/api/quizzes/generate', { method: 'POST', body: JSON.stringify(payload) });
      hideLoading();
      btn.disabled = false; btn.textContent = 'Generate Quiz';

      if (!ok || data.error) {
        showToast(data.error || 'Quiz generation failed', 'error'); return;
      }
      currentQuiz = data.quiz;
      renderQuiz(currentQuiz);
      quizArea.classList.remove('hidden');
      document.getElementById('quiz-section').scrollIntoView({ behavior: 'smooth' });
    });
  }

  function renderQuiz(quiz) {
    quizArea.innerHTML = `
      <div class="card mb-2">
        <div class="card-header">📝 ${quiz.topic} — ${quiz.question_count} Questions</div>
        <div class="card-body" id="questions-container"></div>
        <div class="card-footer flex justify-between items-center">
          <span class="text-muted text-sm">Select one answer per question then submit.</span>
          <button class="btn btn-primary" onclick="submitQuiz()">Submit Quiz</button>
        </div>
      </div>`;
    const qc = document.getElementById('questions-container');
    (quiz.questions || []).forEach((q, i) => {
      const div = document.createElement('div');
      div.className = 'mb-3';
      div.innerHTML = `<p class="fw-700 mb-1">${i + 1}. ${q.question}</p>
        <div id="opts-${i}">${(q.options || []).map((opt, j) => {
          const letter = ['A','B','C','D'][j] || j;
          return `<div class="quiz-option" data-qi="${i}" data-letter="${letter}" onclick="selectOption(this,${i},'${letter}')">
            <span class="option-letter">${letter}</span> ${opt.replace(/^[A-D]\.\s*/,'')}
          </div>`;
        }).join('')}</div>`;
      qc.appendChild(div);
    });
  }
});

function selectOption(el, qi, letter) {
  document.querySelectorAll(`[data-qi="${qi}"]`).forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
  selectedAnswers[qi] = letter;
}

async function submitQuiz() {
  if (!currentQuiz) return;
  const answers = Object.entries(selectedAnswers).map(([qi, letter]) => ({ question_index: parseInt(qi), selected: letter }));
  if (answers.length < (currentQuiz.question_count || 1)) {
    const unanswered = (currentQuiz.question_count || 0) - answers.length;
    if (!confirm(`You have ${unanswered} unanswered question(s). Submit anyway?`)) return;
  }
  showLoading('Scoring quiz...');
  const { ok, data } = await api(`/api/quizzes/${currentQuiz.id}/submit`, { method: 'POST', body: JSON.stringify({ answers }) });
  hideLoading();
  if (!ok) { showToast('Submission failed', 'error'); return; }
  renderResults(data);
}

function renderResults(data) {
  const resultArea = document.getElementById('result-area');
  resultArea.classList.remove('hidden');
  const scoreClass = data.percentage >= 70 ? 'badge-success' : data.percentage >= 50 ? 'badge-warning' : 'badge-danger';
  let html = `<div class="card mb-2">
    <div class="card-header">🏆 Quiz Result</div>
    <div class="card-body">
      <div class="text-center mb-2">
        <div class="stat-number">${data.percentage}%</div>
        <div class="text-muted">Score: ${data.score} / ${data.total}</div>
      </div>
      ${data.weak_topics.length ? `<div class="alert alert-warning mb-2">⚠️ Weak topics: ${data.weak_topics.join(', ')}</div>` : ''}
      ${data.strong_topics.length ? `<div class="alert alert-success mb-2">✅ Strong topics: ${data.strong_topics.join(', ')}</div>` : ''}
      <h3 class="mb-1">Detailed Results</h3>`;

  (data.detailed || []).forEach((d, i) => {
    const icon = d.is_correct ? '✅' : '❌';
    html += `<div class="mb-2 p-2" style="border:1px solid var(--border);border-radius:8px;">
      <p class="fw-700">${icon} ${i + 1}. ${d.question}</p>
      <p class="text-sm">Your answer: <span class="badge ${d.is_correct ? 'badge-success' : 'badge-danger'}">${d.submitted || 'Not answered'}</span>
      ${!d.is_correct ? `· Correct: <span class="badge badge-success">${d.correct_answer}</span>` : ''}</p>
      ${d.explanation ? `<p class="text-sm text-muted">${d.explanation}</p>` : ''}
    </div>`;
  });

  html += `</div><div class="card-footer"><a href="/quiz" class="btn btn-primary">New Quiz</a> <a href="/revision" class="btn btn-outline ml-1">Get Revision Material</a></div></div>`;
  resultArea.innerHTML = html;
  resultArea.scrollIntoView({ behavior: 'smooth' });
}
