/* auth.js */
document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('register-form');
  const loginForm = document.getElementById('login-form');

  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = registerForm.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Creating account...';
      clearErrors();
      const payload = {
        name: registerForm.name.value.trim(),
        email: registerForm.email.value.trim(),
        password: registerForm.password.value,
        confirm_password: registerForm.confirm_password.value,
      };
      const { ok, data } = await api('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
      if (ok) {
        Auth.setToken(data.token);
        Auth.setUser(data.user);
        showToast('Account created! Welcome to StudyGenie AI 🎉', 'success');
        setTimeout(() => window.location.href = '/dashboard', 800);
      } else {
        showError(data.error || 'Registration failed');
        btn.disabled = false; btn.textContent = 'Create Account';
      }
    });
  }

  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = loginForm.querySelector('[type=submit]');
      btn.disabled = true; btn.textContent = 'Signing in...';
      clearErrors();
      const payload = { email: loginForm.email.value.trim(), password: loginForm.password.value };
      const { ok, data } = await api('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
      if (ok) {
        Auth.setToken(data.token);
        Auth.setUser(data.user);
        showToast('Welcome back!', 'success');
        setTimeout(() => window.location.href = '/dashboard', 500);
      } else {
        showError(data.error || 'Login failed');
        btn.disabled = false; btn.textContent = 'Sign In';
      }
    });
  }

  function showError(msg) {
    let el = document.getElementById('auth-error');
    if (!el) return;
    el.textContent = msg; el.style.display = 'block';
  }
  function clearErrors() {
    let el = document.getElementById('auth-error');
    if (el) el.style.display = 'none';
  }
});
