/* main.js — shared utilities */

// ── Token storage ──────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem('sg_token'),
  setToken: (t) => localStorage.setItem('sg_token', t),
  removeToken: () => localStorage.removeItem('sg_token'),
  getUser: () => { try { return JSON.parse(localStorage.getItem('sg_user') || 'null'); } catch { return null; } },
  setUser: (u) => localStorage.setItem('sg_user', JSON.stringify(u)),
  removeUser: () => localStorage.removeItem('sg_user'),
  isLoggedIn: () => !!localStorage.getItem('sg_token'),
};

// ── API helper ─────────────────────────────────────────
async function api(path, options = {}) {
  const token = Auth.getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const resp = await fetch(path, { ...options, headers });
  const data = await resp.json().catch(() => ({}));
  if (resp.status === 401) {
    Auth.removeToken(); Auth.removeUser();
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
      window.location.href = '/login';
    }
  }
  return { ok: resp.ok, status: resp.status, data };
}

async function apiForm(path, formData) {
  const token = Auth.getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const resp = await fetch(path, { method: 'POST', headers, body: formData });
  const data = await resp.json().catch(() => ({}));
  return { ok: resp.ok, status: resp.status, data };
}

// ── Toast ──────────────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(100%)'; toast.style.transition = '0.3s'; setTimeout(() => toast.remove(), 300); }, duration);
}

// ── Loading ────────────────────────────────────────────
function showLoading(msg = 'Loading...') {
  let el = document.getElementById('global-loading');
  if (!el) {
    el = document.createElement('div');
    el.id = 'global-loading';
    el.className = 'loading-overlay';
    el.innerHTML = `<div class="spinner"></div><div style="font-weight:600;color:#4f46e5;">${msg}</div>`;
    document.body.appendChild(el);
  } else {
    el.querySelector('div:last-child').textContent = msg;
    el.style.display = 'flex';
  }
}
function hideLoading() {
  const el = document.getElementById('global-loading');
  if (el) el.style.display = 'none';
}

// ── Sidebar toggle (mobile) ────────────────────────────
function initSidebar() {
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.querySelector('.overlay-backdrop');
  const ham = document.querySelector('.hamburger');
  if (!sidebar) return;
  ham && ham.addEventListener('click', () => { sidebar.classList.toggle('open'); backdrop && backdrop.classList.toggle('open'); });
  backdrop && backdrop.addEventListener('click', () => { sidebar.classList.remove('open'); backdrop.classList.remove('open'); });
}

// ── Active nav link ────────────────────────────────────
function setActiveNav() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(l => {
    l.classList.toggle('active', l.getAttribute('href') === path);
  });
}

// ── Logout ─────────────────────────────────────────────
async function logout() {
  await api('/api/auth/logout', { method: 'POST' });
  Auth.removeToken(); Auth.removeUser();
  window.location.href = '/';
}

// ── Protect pages ──────────────────────────────────────
function requireAuth() {
  if (!Auth.isLoggedIn()) window.location.href = '/login';
}

// ── Render AI output with basic markdown ───────────────
function renderAI(text, container) {
  if (!container) return;
  let html = text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');
  container.innerHTML = `<div class="ai-output"><p>${html}</p></div>`;
}

// ── Subject selector helper ────────────────────────────
async function populateSubjectSelect(selectEl, placeholder = 'All Subjects') {
  const { ok, data } = await api('/api/subjects');
  if (!ok) return;
  selectEl.innerHTML = `<option value="">${placeholder}</option>`;
  (data.subjects || []).forEach(s => {
    const opt = document.createElement('option');
    opt.value = s.id; opt.textContent = s.name;
    selectEl.appendChild(opt);
  });
}

// ── DOMContentLoaded init ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  setActiveNav();
  // Show user name in top bar
  const user = Auth.getUser();
  const userNameEl = document.getElementById('user-display-name');
  if (userNameEl && user) userNameEl.textContent = user.name;
});
