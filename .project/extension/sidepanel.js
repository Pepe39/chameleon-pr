document.addEventListener('DOMContentLoaded', async () => {
  const $ = id => document.getElementById(id);
  const pageStatusText = $('pageStatusText');
  const pageStatusDot = $('pageStatusDot');
  const taskInfo = $('taskInfo');
  const taskIdEl = $('taskId');
  const scrapePreview = $('scrapePreview');
  const inputsList = $('inputsList');
  const missingWarn = $('missingWarn');
  const runBtn = $('runBtn');
  const fillBtn = $('fillBtn');
  const refreshBtn = $('refreshBtn');
  const deleteBtn = $('deleteBtn');
  const progress = $('progress');
  const progressText = $('progressText');
  const statusEl = $('status');
  const resultsCard = $('resultsCard');
  const resultsList = $('resultsList');
  const wrongPage = $('wrongPage');
  const apiUrlInput = $('apiUrl');
  const saveApiBtn = $('saveApiBtn');
  const apiStatusDot = $('apiStatusDot');

  const PLATFORM_HOST = 'annotation-platform-henna.vercel.app';
  let scrapeData = null;
  let deliverables = null;

  // ============ Tabs ============
  document.querySelectorAll('.tab').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(x => x.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      $(`tab-${t.dataset.tab}`).classList.add('active');
    });
  });

  // ============ Config ============
  const stored = await chrome.storage.local.get(['apiUrl']);
  apiUrlInput.value = stored.apiUrl || 'http://localhost:5002';
  saveApiBtn.addEventListener('click', async () => {
    await chrome.storage.local.set({ apiUrl: apiUrlInput.value });
    checkApi();
  });
  async function getApi() {
    const s = await chrome.storage.local.get(['apiUrl']);
    return s.apiUrl || 'http://localhost:5002';
  }
  async function checkApi() {
    try {
      const r = await fetch(`${await getApi()}/status`, { signal: AbortSignal.timeout(2500) });
      apiStatusDot.className = `status-dot ${r.ok ? 'connected' : 'disconnected'}`;
    } catch {
      apiStatusDot.className = 'status-dot disconnected';
    }
  }
  checkApi();

  // ============ Helpers ============
  function showStatus(msg, type = 'info') {
    statusEl.textContent = msg;
    statusEl.className = `status ${type}`;
    statusEl.classList.remove('hidden');
    if (type === 'success') setTimeout(() => statusEl.classList.add('hidden'), 4000);
  }
  function hideAll() {
    [taskInfo, scrapePreview, runBtn, fillBtn, refreshBtn, deleteBtn,
     progress, statusEl, resultsCard, wrongPage].forEach(e => e.classList.add('hidden'));
  }

  function renderInputs(data) {
    inputsList.innerHTML = '';
    const VARS = ['pull_request_url','nwo','head_sha','comment_id','body','file_path','diff_line','discussion_url','repo_url','coding_language'];
    for (const k of VARS) {
      const v = data[k] || '';
      const row = document.createElement('div');
      row.className = 'input-row';
      row.innerHTML = `<span class="k">${k}</span><span class="v ${v ? '' : 'empty'}">${v ? escapeHtml(v.substring(0, 80)) : '(empty)'}</span>`;
      inputsList.appendChild(row);
    }
    if (data._missing && data._missing.length) {
      missingWarn.textContent = `Missing: ${data._missing.join(', ')}`;
      missingWarn.classList.remove('hidden');
    } else {
      missingWarn.classList.add('hidden');
    }
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }

  function renderDeliverables(d) {
    deliverables = d;
    resultsList.innerHTML = '';
    const axes = [
      ['Quality', d.quality],
      ['Severity', d.severity],
      ['Context Scope', d.context_scope],
      ['Advanced', d.advanced],
    ];
    for (const [name, axis] of axes) {
      if (!axis) continue;
      const div = document.createElement('div');
      div.className = 'deliv';
      let entriesHtml = '';
      if (axis.entries && axis.entries.length) {
        entriesHtml = '<div class="deliv-text">' +
          axis.entries.map(e => `${e.diff_line || '-'} | ${e.file_path || '-'} | ${e.why || ''}`).join('\n') +
          '</div>';
      }
      div.innerHTML = `
        <div class="deliv-title">${name}</div>
        <div class="deliv-label">${axis.label || ''}</div>
        <div class="deliv-text">${escapeHtml(axis.reasoning || '')}</div>
        ${entriesHtml}
      `;
      resultsList.appendChild(div);
    }
    resultsCard.classList.remove('hidden');
    fillBtn.classList.remove('hidden');
  }

  // ============ Detect & Scrape ============
  async function detect() {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.url?.includes(PLATFORM_HOST) || !tab.url.includes('/tasks/')) {
        hideAll();
        wrongPage.classList.remove('hidden');
        pageStatusText.textContent = 'Not on a task page';
        pageStatusDot.className = 'status-dot disconnected';
        scrapeData = null;
        return;
      }
      pageStatusText.textContent = 'Scraping...';
      pageStatusDot.className = 'status-dot disconnected';

      const data = await chrome.runtime.sendMessage({ action: 'scrapeTask', tabId: tab.id });
      if (!data || data.error) {
        hideAll();
        showStatus(data?.error || 'Scrape failed', 'error');
        pageStatusText.textContent = 'Scrape failed';
        return;
      }

      scrapeData = data;
      hideAll();
      taskIdEl.textContent = data.task_id;
      taskInfo.classList.remove('hidden');
      renderInputs(data);
      scrapePreview.classList.remove('hidden');
      runBtn.classList.remove('hidden');

      // Check existing task on the API
      try {
        const api = await getApi();
        const r = await fetch(`${api}/run/status/${data.task_id}`);
        const s = await r.json();
        if (s.status === 'done' && s.deliverables) {
          renderDeliverables(s.deliverables);
          deleteBtn.classList.remove('hidden');
          refreshBtn.classList.remove('hidden');
          pageStatusText.textContent = 'Already labeled';
          pageStatusDot.className = 'status-dot connected';
        } else if (s.status === 'running') {
          progress.classList.remove('hidden');
          progressText.textContent = 'Running...';
          pageStatusText.textContent = 'Running...';
          pollStatus(api, data.task_id);
        } else {
          pageStatusText.textContent = 'Ready';
          pageStatusDot.className = 'status-dot connected';
        }
      } catch {
        pageStatusText.textContent = 'API unreachable';
      }
    } catch (err) {
      showStatus(err.message, 'error');
    }
  }

  detect();
  chrome.tabs.onActivated?.addListener(() => setTimeout(detect, 400));
  chrome.tabs.onUpdated?.addListener((_id, info) => {
    if (info.status === 'complete') setTimeout(detect, 400);
  });

  // ============ Run ============
  runBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    runBtn.classList.add('hidden');
    progress.classList.remove('hidden');
    progressText.textContent = 'Sending to API...';
    try {
      const api = await getApi();
      const r = await fetch(`${api}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(scrapeData),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.error || `HTTP ${r.status}`);
      }
      const s = await r.json();
      if (s.status === 'done' && s.deliverables) {
        progress.classList.add('hidden');
        renderDeliverables(s.deliverables);
        deleteBtn.classList.remove('hidden');
        return;
      }
      progressText.textContent = 'Claude is labeling...';
      pollStatus(api, scrapeData.task_id);
    } catch (err) {
      progress.classList.add('hidden');
      runBtn.classList.remove('hidden');
      showStatus(err.message, 'error');
    }
  });

  async function pollStatus(api, tid) {
    for (let i = 0; i < 240; i++) {
      await new Promise(r => setTimeout(r, 3000));
      if (scrapeData?.task_id !== tid) return;
      progressText.textContent = `Labeling... ${i * 3}s`;
      try {
        const r = await fetch(`${api}/run/status/${tid}`);
        const s = await r.json();
        if (s.status === 'done' && s.deliverables) {
          progress.classList.add('hidden');
          renderDeliverables(s.deliverables);
          deleteBtn.classList.remove('hidden');
          refreshBtn.classList.remove('hidden');
          pageStatusText.textContent = 'Labeled';
          pageStatusDot.className = 'status-dot connected';
          return;
        }
        if (s.status === 'error') throw new Error(s.error || 'Pipeline failed');
      } catch (err) {
        if (err.message !== 'Failed to fetch') {
          progress.classList.add('hidden');
          runBtn.classList.remove('hidden');
          showStatus(err.message, 'error');
          return;
        }
      }
    }
    progress.classList.add('hidden');
    runBtn.classList.remove('hidden');
    showStatus('Timeout', 'error');
  }

  // ============ Fill ============
  fillBtn.addEventListener('click', async () => {
    if (!deliverables) return;
    fillBtn.disabled = true;
    fillBtn.textContent = 'Filling...';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const r = await chrome.runtime.sendMessage({
        action: 'fillDeliverables', tabId: tab.id, data: deliverables
      });
      if (r.error) throw new Error(r.error);
      showStatus(`Filled ${r.filled} fields${r.errors.length ? '. Issues: ' + r.errors.join('; ') : ''}`,
                 r.errors.length ? 'info' : 'success');
    } catch (err) {
      showStatus(err.message, 'error');
    }
    fillBtn.textContent = 'Fill Deliverables';
    fillBtn.disabled = false;
  });

  // ============ Refresh / Delete ============
  refreshBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    const api = await getApi();
    const r = await fetch(`${api}/run/status/${scrapeData.task_id}`);
    const s = await r.json();
    if (s.status === 'done' && s.deliverables) {
      renderDeliverables(s.deliverables);
      showStatus('Refreshed', 'success');
    } else {
      showStatus('No deliverables yet', 'info');
    }
  });

  deleteBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    const api = await getApi();
    const r = await fetch(`${api}/task/${scrapeData.task_id}`, { method: 'DELETE' });
    if (r.ok) {
      deliverables = null;
      resultsCard.classList.add('hidden');
      fillBtn.classList.add('hidden');
      deleteBtn.classList.add('hidden');
      refreshBtn.classList.add('hidden');
      runBtn.classList.remove('hidden');
      showStatus('Task deleted', 'success');
    } else {
      showStatus('Delete failed', 'error');
    }
  });
});
