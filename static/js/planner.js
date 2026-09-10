/* planner.js */
document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();
  await populateSubjectSelect(document.getElementById('plan-subject'));
  loadLatestPlan();

  const form = document.getElementById('plan-form');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = e.target.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Generating Plan...';
      showLoading('Creating your personalized study plan...');
      const payload = {
        subject_id: document.getElementById('plan-subject').value,
        hours_per_day: parseFloat(document.getElementById('hours-per-day').value) || 2,
        duration_days: parseInt(document.getElementById('duration-days').value) || 7,
        exam_date: document.getElementById('exam-date').value || null,
      };
      const { ok, data } = await api('/api/planner/generate', { method: 'POST', body: JSON.stringify(payload) });
      hideLoading();
      btn.disabled = false; btn.textContent = 'Generate Plan';
      if (!ok || data.error) { showToast(data.error || 'Plan generation failed', 'error'); return; }
      showToast('Study plan generated!', 'success');
      renderPlan(data.plan);
    });
  }

  async function loadLatestPlan() {
    const { ok, data } = await api('/api/planner/latest');
    if (ok && data.plan) renderPlan(data.plan);
  }

  function renderPlan(plan) {
    const el = document.getElementById('plan-display');
    if (!el) return;
    if (!plan || !plan.tasks || !plan.tasks.length) {
      el.innerHTML = '<p class="text-muted">No study plan yet. Generate one above.</p>'; return;
    }
    let html = `<div class="card"><div class="card-header">📅 Study Plan — ${plan.duration_days} Days</div><div class="card-body">`;
    plan.tasks.forEach((day, di) => {
      const tasks = day.tasks || [];
      html += `<div class="mb-2"><h3 class="mb-1" style="font-size:15px;">Day ${day.day || di+1} — ${day.date || ''}</h3>`;
      tasks.forEach((t, ti) => {
        html += `<div class="flex items-center gap-1 mb-1" style="background:var(--bg);padding:10px;border-radius:8px;">
          <input type="checkbox" ${t.completed ? 'checked' : ''} onchange="markTask('${plan.id}',${di},${ti},this)">
          <span class="badge badge-primary">${t.subject || ''}</span>
          <span class="text-sm flex-1">${t.topic || ''} — ${t.activity || ''}</span>
          <span class="badge badge-gray">${t.duration_minutes || 0} min</span>
        </div>`;
      });
      html += `</div>`;
    });
    html += `</div></div>`;
    el.innerHTML = html;
  }
});

async function markTask(planId, dayIdx, taskIdx, checkbox) {
  const flatIdx = dayIdx * 100 + taskIdx; // simplified index
  const { ok } = await api(`/api/planner/${planId}/task/${taskIdx}/complete`, { method: 'POST' });
  if (!ok) { checkbox.checked = !checkbox.checked; showToast('Could not update task', 'error'); }
}
