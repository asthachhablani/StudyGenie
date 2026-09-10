/* dashboard.js */
document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();
  showLoading('Loading dashboard...');

  const { ok, data } = await api('/api/dashboard');
  hideLoading();

  if (!ok) { showToast('Could not load dashboard data', 'error'); return; }

  const s = data.stats || {};
  setText('stat-subjects', s.total_subjects ?? 0);
  setText('stat-docs', s.total_documents ?? 0);
  setText('stat-quizzes', s.total_quizzes ?? 0);
  setText('stat-score', (s.avg_score ?? 0) + '%');
  setText('stat-completed', s.topics_completed ?? 0);

  // Subjects list
  const subList = document.getElementById('subject-list');
  if (subList) {
    const subs = data.subjects || [];
    subList.innerHTML = subs.length
      ? subs.map(s => `<a href="/subjects/${s.id}" class="nav-link">${s.name}</a>`).join('')
      : '<p class="text-muted text-sm">No subjects yet. <a href="/subjects">Create one</a>.</p>';
  }

  // Weak topics
  renderTopicList('weak-topics-list', data.weak_topics || [], 'badge-danger', 'Needs attention');
  renderTopicList('strong-topics-list', data.strong_topics || [], 'badge-success', 'Strong');

  // Today tasks
  const tasksEl = document.getElementById('today-tasks');
  if (tasksEl) {
    const tasks = data.today_tasks || [];
    tasksEl.innerHTML = tasks.length
      ? tasks.map(t => `<div class="flex items-center gap-1 mb-1">
          <span class="badge badge-info">${t.subject || ''}</span>
          <span class="text-sm">${t.topic || t.activity || ''} · ${t.duration_minutes || 0} min</span>
        </div>`).join('')
      : '<p class="text-muted text-sm">No tasks. <a href="/study-plan">Generate a study plan</a>.</p>';
  }

  // Recent results
  const resultsEl = document.getElementById('recent-results');
  if (resultsEl) {
    const results = data.recent_results || [];
    resultsEl.innerHTML = results.length
      ? results.map(r => `<div class="flex justify-between items-center mb-1">
          <span class="text-sm">${r.percentage}%</span>
          <div class="progress-bar-track flex-1 mx-2"><div class="progress-bar-fill" style="width:${r.percentage}%"></div></div>
          <span class="text-sm text-muted">${r.score}/${r.total}</span>
        </div>`).join('')
      : '<p class="text-muted text-sm">No quizzes attempted yet.</p>';
  }

  // Exam dates countdown
  const examEl = document.getElementById('exam-countdown');
  if (examEl) {
    const exams = data.exam_dates || {};
    const entries = Object.entries(exams);
    if (entries.length) {
      examEl.innerHTML = entries.map(([sub, date]) => {
        const days = Math.ceil((new Date(date) - new Date()) / 86400000);
        const badge = days <= 7 ? 'badge-danger' : days <= 14 ? 'badge-warning' : 'badge-info';
        return `<div class="flex items-center gap-1 mb-1">
          <span class="badge ${badge}">${days > 0 ? days + ' days' : 'Today!'}</span>
          <span class="text-sm">${sub} exam</span>
        </div>`;
      }).join('');
    } else {
      examEl.innerHTML = '<p class="text-muted text-sm">No exam dates set. <a href="/profile">Set exam date</a>.</p>';
    }
  }

  function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
  function renderTopicList(id, topics, badgeClass, label) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = topics.length
      ? topics.map(t => `<span class="badge ${badgeClass} mb-1">${t}</span> `).join('')
      : `<p class="text-muted text-sm">No ${label.toLowerCase()} topics yet.</p>`;
  }
});
