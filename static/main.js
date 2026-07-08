/* ─────────────────────────────────────────────────────────────────────────────
   main.js  —  Technical Debug Assistant
   Handles: starfield canvas, status polling, chat UI, markdown rendering
───────────────────────────────────────────────────────────────────────────── */

/* ── Starfield ─────────────────────────────────────────────────────────────── */
(function () {
  const canvas = document.getElementById('starfield');
  const ctx    = canvas.getContext('2d');
  let W, H, stars = [];

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }

  function initStars() {
    stars = [];
    for (let i = 0; i < 280; i++) {
      stars.push({
        x:     Math.random() * W,
        y:     Math.random() * H,
        r:     Math.random() * 1.4 + 0.2,
        a:     Math.random(),
        s:     Math.random() * 0.004 + 0.001,
        phase: Math.random() * Math.PI * 2,
      });
    }
  }

  let t = 0;
  function draw() {
    ctx.clearRect(0, 0, W, H);
    t += 0.012;
    stars.forEach(star => {
      const alpha = 0.3 + 0.7 * (0.5 + 0.5 * Math.sin(t * star.s * 60 + star.phase));
      ctx.beginPath();
      ctx.arc(star.x, star.y, star.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200, 220, 255, ${alpha * star.a})`;
      ctx.fill();
    });
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', () => { resize(); initStars(); });
  resize(); initStars(); draw();
})();


/* ── Status polling ────────────────────────────────────────────────────────── */
const pill  = document.getElementById('status-pill');
const label = document.getElementById('status-label');
let isReady = false;

async function pollStatus() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();
    if (d.ready) {
      pill.className       = 'ready';
      label.textContent    = 'Ready';
      isReady              = true;
      document.getElementById('send-btn').disabled = false;
    } else if (d.error) {
      pill.className    = 'error';
      label.textContent = 'Error';
      showToast('Pipeline error: ' + d.error, 'error');
    } else {
      setTimeout(pollStatus, 1500);
    }
  } catch {
    setTimeout(pollStatus, 2000);
  }
}

document.getElementById('send-btn').disabled = true;
pollStatus();


/* ── Auto-resize textarea ──────────────────────────────────────────────────── */
function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 150) + 'px';
}


/* ── Key handler ───────────────────────────────────────────────────────────── */
function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendQuestion();
  }
}


/* ── Chip click ────────────────────────────────────────────────────────────── */
function useChip(el) {
  const input = document.getElementById('question-input');
  input.value = el.textContent.trim();
  autoResize(input);
  input.focus();
}


/* ── Toast notification ────────────────────────────────────────────────────── */
function showToast(msg, type = 'success') {
  const t = document.createElement('div');
  t.className   = `toast ${type}`;
  t.textContent = msg;
  document.getElementById('toast-container').appendChild(t);
  setTimeout(() => t.remove(), 3500);
}


/* ── HTML escape ───────────────────────────────────────────────────────────── */
function escHtml(str) {
  return str
    .replace(/&/g,  '&amp;')
    .replace(/</g,  '&lt;')
    .replace(/>/g,  '&gt;');
}


/* ── Markdown renderer ─────────────────────────────────────────────────────── */
function renderMarkdown(text) {
  // Fenced code blocks — strip optional language tag, show header bar
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const langLabel = lang ? lang.trim() : '';
    const dots      = `<span class="code-dots"><span></span><span></span><span></span></span>`;
    const langSpan  = langLabel ? `<span class="code-lang">${escHtml(langLabel)}</span>` : '';
    const header    = `<div class="code-header">${dots}${langSpan}</div>`;
    return `<pre>${header}<code>${escHtml(code.trim())}</code></pre>`;
  });

  // Inline code
  text = text.replace(/`([^`]+)`/g, (_, c) => `<code>${escHtml(c)}</code>`);

  // Bold / italic
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*(.+?)\*/g,     '<em>$1</em>');

  // Headings
  text = text.replace(/^### (.+)$/gm, '<h4 style="color:var(--accent-cyan);margin:10px 0 4px;">$1</h4>');
  text = text.replace(/^## (.+)$/gm,  '<h3 style="color:var(--accent-blue);margin:12px 0 4px;">$1</h3>');

  // Bullet lists
  text = text.replace(/^[-*] (.+)$/gm, '<li style="margin-left:18px;margin-bottom:3px;">$1</li>');
  text = text.replace(/(<li[\s\S]*?<\/li>\n?)+/g, s => `<ul style="margin:8px 0;">${s}</ul>`);

  // Paragraph breaks
  text = text.replace(/\n\n/g, '</p><p style="margin-top:10px;">');

  return `<p>${text}</p>`;
}


/* ── Append user message ───────────────────────────────────────────────────── */
function appendUser(question) {
  hideWelcome();
  const feed = document.getElementById('chat-feed');
  const div  = document.createElement('div');
  div.className = 'message msg-user';
  div.innerHTML = `<div class="bubble">${escHtml(question)}</div>`;
  feed.appendChild(div);
  scrollFeed();
}


/* ── Append thinking placeholder ───────────────────────────────────────────── */
function appendThinking() {
  const feed = document.getElementById('chat-feed');
  const div  = document.createElement('div');
  div.id        = 'thinking-msg';
  div.className = 'message msg-ai';
  div.innerHTML = `
    <div class="ai-avatar">🤖</div>
    <div class="content">
      <div class="thinking">
        <div class="thinking-dots"><span></span><span></span><span></span></div>
        <span class="thinking-text">Searching knowledge base…</span>
      </div>
    </div>`;
  feed.appendChild(div);
  scrollFeed();
}


/* ── Append AI answer ──────────────────────────────────────────────────────── */
function appendAnswer(data) {
  document.getElementById('thinking-msg')?.remove();

  const feed = document.getElementById('chat-feed');
  const div  = document.createElement('div');
  div.className = 'message msg-ai';

  const sourcesHtml = data.sources?.length ? buildSourcesHtml(data.sources) : '';

  div.innerHTML = `
    <div class="ai-avatar">🤖</div>
    <div class="content">
      <div class="meta">
        <span class="name">Debug AI</span>
        <span class="time">${data.timestamp}</span>
        <span class="elapsed">⏱ ${data.elapsed}s</span>
      </div>
      <div class="answer-card">
        <div class="answer-text">${renderMarkdown(data.answer)}</div>
        ${sourcesHtml}
      </div>
    </div>`;
  feed.appendChild(div);
  scrollFeed();
}


/* ── Build sources HTML ────────────────────────────────────────────────────── */
function buildSourcesHtml(sources) {
  const items = sources.map(s => `
    <div class="source-item">
      <div class="source-header">
        <span class="source-file">📄 ${escHtml(s.file)}</span>
        <span class="score-badge">score ${s.score}</span>
      </div>
      ${s.headings.length ? `
      <div class="source-headings">
        ${s.headings.map(h => `<span class="heading-tag">${escHtml(h)}</span>`).join('')}
      </div>` : ''}
    </div>`).join('');

  return `
    <div class="sources">
      <button class="sources-toggle" onclick="toggleSources(this)">
        <span>📚 Sources (${sources.length})</span>
        <em class="chevron">▾</em>
      </button>
      <div class="sources-body">${items}</div>
    </div>`;
}

function toggleSources(btn) {
  btn.classList.toggle('open');
  btn.nextElementSibling.classList.toggle('open');
}


/* ── Append error ──────────────────────────────────────────────────────────── */
function appendError(msg) {
  document.getElementById('thinking-msg')?.remove();

  const feed = document.getElementById('chat-feed');
  const div  = document.createElement('div');
  div.className = 'message msg-ai';
  div.innerHTML = `
    <div class="ai-avatar">🤖</div>
    <div class="content">
      <div class="error-bubble">
        <span class="err-icon">⚠️</span>
        <span class="err-text">${escHtml(msg)}</span>
      </div>
    </div>`;
  feed.appendChild(div);
  scrollFeed();
}


/* ── Send question ─────────────────────────────────────────────────────────── */
let busy = false;

async function sendQuestion() {
  if (busy) return;
  if (!isReady) { showToast('Pipeline is still loading…', 'error'); return; }

  const input    = document.getElementById('question-input');
  const question = input.value.trim();
  if (!question) return;

  busy = true;
  document.getElementById('send-btn').disabled = true;
  input.value       = '';
  input.style.height = 'auto';

  appendUser(question);
  appendThinking();

  try {
    const res  = await fetch('/api/ask', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ question }),
    });
    const data = await res.json();

    if (!res.ok) {
      appendError(data.detail || data.error || 'Something went wrong.');
    } else {
      appendAnswer(data);
    }
  } catch {
    appendError('Network error — make sure the server is running.');
  } finally {
    busy = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('question-input').focus();
  }
}


/* ── Clear history ─────────────────────────────────────────────────────────── */
async function clearHistory() {
  try {
    await fetch('/api/clear', { method: 'POST' });
    const feed = document.getElementById('chat-feed');
    feed.innerHTML = '';
    showWelcome(feed);
    showToast('Session cleared', 'success');
  } catch {
    showToast('Could not clear history', 'error');
  }
}


/* ── Welcome helpers ───────────────────────────────────────────────────────── */
function hideWelcome() {
  document.getElementById('welcome-screen')?.remove();
}

function showWelcome(feed) {
  feed.innerHTML = `
    <div class="welcome" id="welcome-screen">
      <div class="welcome-orb"><span>🐛</span></div>
      <h2>What shall we debug today?</h2>
      <p>Ask a technical question. I'll search through the knowledge base and surface a precise, context-grounded answer.</p>
      <div class="suggestion-chips">
        <div class="chip" onclick="useChip(this)">How do I fix a NullPointerException?</div>
        <div class="chip" onclick="useChip(this)">What causes CUDA out-of-memory errors?</div>
        <div class="chip" onclick="useChip(this)">Why is my model not converging?</div>
        <div class="chip" onclick="useChip(this)">How to handle import errors in Python?</div>
      </div>
    </div>`;
}


/* ── Scroll feed to bottom ─────────────────────────────────────────────────── */
function scrollFeed() {
  const feed = document.getElementById('chat-feed');
  feed.scrollTop = feed.scrollHeight;
}


/* ─────────────────────────────────────────────────────────────────────────────
   Upload Panel
───────────────────────────────────────────────────────────────────────────── */

/* ── Panel open / close ────────────────────────────────────────────────────── */
function openUploadPanel() {
  document.getElementById('upload-panel').classList.add('open');
  document.getElementById('panel-overlay').classList.add('visible');
  loadUploadedFiles();
}

function closeUploadPanel() {
  document.getElementById('upload-panel').classList.remove('open');
  document.getElementById('panel-overlay').classList.remove('visible');
}


/* ── Drag & drop ───────────────────────────────────────────────────────────── */
function handleDragOver(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
  document.getElementById('drop-zone').classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
  const files = Array.from(e.dataTransfer.files);
  processFiles(files);
}

function handleFileSelect(e) {
  const files = Array.from(e.target.files);
  processFiles(files);
  e.target.value = '';   // reset so the same file can be re-selected
}


/* ── Process & upload file queue ───────────────────────────────────────────── */
async function processFiles(files) {
  const allowed = files.filter(f =>
    f.name.endsWith('.txt') || f.name.endsWith('.md')
  );

  if (allowed.length === 0) {
    showToast('Only .txt and .md files are supported.', 'error');
    return;
  }

  for (const file of allowed) {
    await uploadFile(file);
  }

  loadUploadedFiles();
}

async function uploadFile(file) {
  const progressEl  = document.getElementById('upload-progress');
  const progressTxt = document.getElementById('upload-progress-text');

  progressEl.classList.add('visible');
  progressTxt.textContent = `Embedding "${file.name}"…`;

  try {
    const form = new FormData();
    form.append('file', file);

    const res  = await fetch('/api/upload', { method: 'POST', body: form });
    const data = await res.json();

    if (!res.ok) {
      showToast(data.detail || 'Upload failed.', 'error');
    } else {
      showToast(`✓ ${data.filename} → ${data.chunks_added} chunk(s) indexed`, 'success');
    }
  } catch {
    showToast(`Network error uploading "${file.name}".`, 'error');
  } finally {
    progressEl.classList.remove('visible');
  }
}


/* ── Load & render file list ───────────────────────────────────────────────── */
async function loadUploadedFiles() {
  try {
    const res   = await fetch('/api/uploads');
    const files = await res.json();
    renderUploadedFiles(files);
    updateBadge(files.length);
  } catch {
    /* silently ignore */
  }
}

function renderUploadedFiles(files) {
  const list = document.getElementById('upload-file-list');

  if (!files.length) {
    list.innerHTML = '<div class="upload-empty">No files uploaded yet.</div>';
    return;
  }

  list.innerHTML = files.map(f => `
    <div class="upload-file-item">
      <span class="upload-file-icon">${f.name.endsWith('.md') ? '📝' : '📄'}</span>
      <div class="upload-file-info">
        <div class="upload-file-name" title="${escHtml(f.name)}">${escHtml(f.name)}</div>
        <div class="upload-file-meta">${f.size_kb} KB · ${f.chunks} chunk${f.chunks !== 1 ? 's' : ''}</div>
      </div>
      <button
        class="upload-file-delete"
        title="Remove file"
        onclick="deleteUploadedFile('${escHtml(f.name)}')"
      >✕</button>
    </div>`).join('');
}

function updateBadge(count) {
  const badge = document.getElementById('upload-badge');
  badge.textContent = count;
  badge.classList.toggle('visible', count > 0);
}


/* ── Delete uploaded file ──────────────────────────────────────────────────── */
async function deleteUploadedFile(filename) {
  try {
    const res = await fetch(`/api/uploads/${encodeURIComponent(filename)}`, {
      method: 'DELETE',
    });
    if (res.ok) {
      showToast(`"${filename}" removed.`, 'success');
      loadUploadedFiles();
    } else {
      const d = await res.json();
      showToast(d.detail || 'Could not delete file.', 'error');
    }
  } catch {
    showToast('Network error while deleting.', 'error');
  }
}


/* ── Initialise badge on page load ─────────────────────────────────────────── */
loadUploadedFiles();

