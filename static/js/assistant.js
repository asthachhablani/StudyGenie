/* assistant.js */
document.addEventListener('DOMContentLoaded', async () => {
  requireAuth();
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');
  const subjectSel = document.getElementById('chat-subject');

  await populateSubjectSelect(subjectSel, 'Select Subject (optional)');

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = input.value.trim();
      if (!message) return;
      appendMessage(message, 'user');
      input.value = '';
      const btn = form.querySelector('[type=submit]');
      btn.disabled = true;

      const thinkingId = appendThinking();

      const payload = {
        message,
        subject_id: subjectSel ? subjectSel.value : '',
      };
      const { ok, data } = await api('/api/ai/chat', { method: 'POST', body: JSON.stringify(payload) });
      removeThinking(thinkingId);
      btn.disabled = false;

      if (!ok) { appendMessage('Sorry, an error occurred. Please try again.', 'ai'); return; }

      let response = '';
      const intent = data.intent || 'answer';

      if (intent === 'answer') {
        response = data.answer || 'No answer generated.';
      } else if (intent === 'summary') {
        response = data.summary || 'No summary generated.';
      } else if (intent === 'revision') {
        response = data.revision || 'No revision material generated.';
      } else if (intent === 'flashcard') {
        const cards = data.flashcards || [];
        response = cards.length ? `Generated ${cards.length} flashcards! <a href="/flashcards">View Flashcards</a>` : 'No flashcards generated.';
      } else if (intent === 'quiz') {
        const quiz = data.quiz;
        response = quiz ? `Quiz generated: "${quiz.topic}" with ${quiz.question_count} questions. <a href="/quiz">Go to Quiz</a>` : (data.error || 'Quiz generation failed.');
      } else if (intent === 'plan') {
        response = data.plan ? `Study plan generated for ${data.plan.duration_days} days! <a href="/study-plan">View Plan</a>` : (data.error || 'Plan generation failed.');
      } else if (intent === 'weakness') {
        const weak = data.weak_topics || [];
        const recs = data.recommendations || [];
        response = `**Weak topics:** ${weak.join(', ') || 'None identified yet'}\n\n${recs.join('\n')}`;
      } else {
        response = data.answer || JSON.stringify(data);
      }

      appendMessage(response, 'ai');

      if (data.sources && data.sources.length) {
        const srcHtml = data.sources.map(s => `📄 ${s.filename} (p.${s.page_number})`).join('<br>');
        appendMessage(`**Sources:**<br>${srcHtml}`, 'ai', 'source');
      }
    });
  }

  function appendMessage(text, role, cls = '') {
    const div = document.createElement('div');
    div.className = `chat-msg ${role}${cls ? ' ' + cls : ''}`;
    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🤖';
    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble';
    renderAI(text, bubble);
    div.appendChild(avatar);
    div.appendChild(bubble);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  function appendThinking() {
    const id = 'thinking-' + Date.now();
    const div = document.createElement('div');
    div.id = id; div.className = 'chat-msg ai';
    div.innerHTML = `<div class="chat-avatar">🤖</div><div class="chat-bubble text-muted"><span class="spinner" style="width:16px;height:16px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:6px;"></span> Thinking...</div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return id;
  }
  function removeThinking(id) { const el = document.getElementById(id); if (el) el.remove(); }
});
