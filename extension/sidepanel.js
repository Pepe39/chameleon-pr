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
  const reviewBtn = $('reviewBtn');
  const fillBtn = $('fillBtn');
  const applyFixesBtn = $('applyFixesBtn');
  const reevaluateBtn = $('reevaluateBtn');
  const clearBtn = $('clearBtn');
  const reviewCard = $('reviewCard');
  const reviewChanges = $('reviewChanges');
  const reviewFeedback = $('reviewFeedback');
  const statusBtn = $('statusBtn');
  const recheckBtn = $('recheckBtn');
  const resyncBtn = $('resyncBtn');
  const statusCard = $('statusCard');
  const statusBody = $('statusBody');
  let reviewFixes = null;
  let reviewMeta = { quality_score: null, feedback_text: '' };
  const progress = $('progress');
  const progressText = $('progressText');
  const statusEl = $('status');
  const resultsCard = $('resultsCard');
  const resultsList = $('resultsList');
  const wrongPage = $('wrongPage');
  const apiUrlInput = $('apiUrl');
  const saveApiBtn = $('saveApiBtn');
  const apiStatusDot = $('apiStatusDot');
  const modelSelect = $('modelSelect');

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
  const stored = await chrome.storage.local.get(['apiUrl', 'model']);
  apiUrlInput.value = stored.apiUrl || 'http://localhost:5002';
  modelSelect.value = stored.model || 'claude-opus-4-6';
  saveApiBtn.addEventListener('click', async () => {
    await chrome.storage.local.set({ apiUrl: apiUrlInput.value });
    checkApi();
  });
  modelSelect.addEventListener('change', async () => {
    await chrome.storage.local.set({ model: modelSelect.value });
  });
  async function getApi() {
    const s = await chrome.storage.local.get(['apiUrl']);
    return s.apiUrl || 'http://localhost:5002';
  }
  async function getModel() {
    const s = await chrome.storage.local.get(['model']);
    return s.model || 'claude-opus-4-6';
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
    [taskInfo, scrapePreview, runBtn, reviewBtn, fillBtn, applyFixesBtn, reevaluateBtn, recheckBtn, clearBtn, statusBtn,
     progress, statusEl, resultsCard, reviewCard, statusCard, wrongPage].forEach(e => e.classList.add('hidden'));
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
    clearBtn.classList.remove('hidden');
    recheckBtn.classList.remove('hidden');
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
      statusBtn.classList.remove('hidden');

      // Detect stage from page DOM (stepper-based)
      const layer = await detectPlatformLayer(tab.id);
      const isReviewStage = layer === 'New Review' || layer === 'QC Layer';
      runBtn.textContent = 'Run /run pipeline';
      reviewBtn.textContent = 'Run /review';
      if (isReviewStage) {
        reviewBtn.classList.remove('hidden');
        pageStatusText.textContent = `${layer} stage`;
        pageStatusDot.className = 'status-dot connected';
        // Re-scrape with the review-aware scraper so we have current axis values for the diff view
        try {
          const enriched = await chrome.runtime.sendMessage({ action: 'scrapeReview', tabId: tab.id });
          if (enriched && !enriched.error) scrapeData = enriched;
        } catch {}
        // Check if we already produced a review for this task
        try {
          const api = await getApi();
          const r = await fetch(`${api}/review/status/${data.task_id}`);
          const s = await r.json();
          if (s.status === 'done') {
            renderReview(s);
            reviewBtn.classList.add('hidden');
            pageStatusText.textContent = 'Review ready';
          }
        } catch {}
        return;
      }

      // Annotation (or unknown) layer -> /run
      pageStatusText.textContent = layer ? `${layer} stage` : 'Ready';
      runBtn.classList.remove('hidden');

      // Check existing task on the API
      try {
        const api = await getApi();
        const r = await fetch(`${api}/run/status/${data.task_id}`);
        const s = await r.json();
        if (s.status === 'done' && s.deliverables) {
          renderDeliverables(s.deliverables);
          runBtn.classList.add('hidden');
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

  resyncBtn.addEventListener('click', () => {
    showStatus('Resyncing...', 'info');
    detect().then(() => showStatus('Resynced', 'success'));
  });

  detect();
  chrome.tabs.onActivated?.addListener(() => setTimeout(detect, 400));
  // The annotation platform is a SPA, so navigating between tasks triggers a
  // URL change but never a full-load "complete". Listen for both.
  chrome.tabs.onUpdated?.addListener((_id, info) => {
    if (info.status === 'complete' || info.url) setTimeout(detect, 400);
  });

  // ============ Run ============
  runBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    runBtn.classList.add('hidden');
    progress.classList.remove('hidden');
    progressText.textContent = 'Sending to API...';
    try {
      const api = await getApi();
      const model = await getModel();
      const r = await fetch(`${api}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...scrapeData, model }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.error || `HTTP ${r.status}`);
      }
      const s = await r.json();
      if (s.status === 'done' && s.deliverables) {
        progress.classList.add('hidden');
        renderDeliverables(s.deliverables);
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

  // ============ Review ============
  async function detectPlatformLayer(tabId) {
    try {
      const [r] = await chrome.scripting.executeScript({
        target: { tabId },
        func: () => {
          // The stepper at the top of the task page has 4 steps: Annotation,
          // New Review, QC Layer, Done. The active step's circle uses a
          // colored Tailwind class (purple-500, blue-500, etc.) with a ring-2
          // highlight. Completed steps use emerald-500. Inactive steps use
          // slate-*. We detect the active step by looking for ring-2 on the
          // circle, and completed steps by emerald-500.
          const STEPS = ['Annotation', 'New Review', 'QC Layer', 'Done'];
          const leaves = document.querySelectorAll('span, div, p, li, button, a');
          let activeStep = '';
          let lastCompleted = '';
          for (const el of leaves) {
            if (el.children.length) continue;
            const t = (el.textContent || '').trim();
            if (!STEPS.includes(t)) continue;
            const parent = el.parentElement;
            if (!parent) continue;
            const circle = parent.querySelector('.rounded-full');
            if (!circle) continue;
            const cls = circle.className || '';
            // Active step has ring-2 (the focus ring)
            if (/ring-2/.test(cls)) { activeStep = t; break; }
            // Completed step uses emerald-500
            if (/emerald-500/.test(cls)) lastCompleted = t;
          }
          // If we found an active step with ring-2, return it
          if (activeStep) return activeStep;
          // Fallback: return the step after the last completed one
          if (lastCompleted) {
            const idx = STEPS.indexOf(lastCompleted);
            if (idx >= 0 && idx < STEPS.length - 1) return STEPS[idx + 1];
          }
          return '';
        },
      });
      return r?.result || '';
    } catch {
      return '';
    }
  }
  async function detectReviewStage(tabId) {
    const layer = await detectPlatformLayer(tabId);
    return layer === 'New Review' || layer === 'QC Layer';
  }

  function escapeMd(s) { return escapeHtml(s || ''); }

  function renderReview(payload) {
    const { feedback = '', fixed = {}, quality_score = null } = payload;
    reviewFixes = fixed && Object.keys(fixed).length ? fixed : null;
    reviewMeta = { quality_score, feedback_text: feedback };

    // Changes summary: list axes that have a fix vs original
    const orig = scrapeData?.current || {};
    const lines = [];
    const axes = [
      ['Quality', 'quality'],
      ['Severity', 'severity'],
      ['Context Scope', 'context_scope'],
      ['Advanced', 'advanced'],
    ];
    for (const [name, key] of axes) {
      const f = fixed[key];
      if (!f) continue;
      const o = orig[key] || {};
      if (key === 'context_scope') {
        lines.push(
          `<div class="deliv-title">${name}</div>` +
          `<div class="deliv-text">label: <b>${escapeMd(o.label)}</b> -> <b>${escapeMd(f.label)}</b></div>` +
          `<div class="deliv-text">${(f.entries || []).length} context entries (was ${(o.entries || []).length})</div>`
        );
      } else {
        const labelChanged = (o.label || '') !== (f.label || '');
        const reasonChanged = (o.reasoning || '') !== (f.reasoning || '');
        let html = `<div class="deliv-title">${name}</div>`;
        if (labelChanged) html += `<div class="deliv-text">label: <b>${escapeMd(o.label)}</b> -> <b>${escapeMd(f.label)}</b></div>`;
        if (reasonChanged) html += `<div class="deliv-text">reasoning updated</div>`;
        if (!labelChanged && !reasonChanged) html += `<div class="deliv-text">(no change)</div>`;
        lines.push(html);
      }
    }
    reviewChanges.innerHTML = lines.length
      ? `<div class="deliv-title">Proposed Changes</div>` + lines.map(l => `<div class="deliv">${l}</div>`).join('')
      : `<div class="deliv-title">Proposed Changes</div><div class="deliv-text">No changes; the original labels passed review.</div>`;

    // Feedback to tasker: API already returns it cleaned and ready to paste
    reviewFeedback.innerHTML =
      `<div class="deliv-title">Note for the tasker</div>` +
      `<pre class="deliv-text" style="white-space:pre-wrap;">${escapeMd(feedback)}</pre>`;

    reviewCard.classList.remove('hidden');
    // Always show apply button (it also fills score + feedback even if no axis fixes)
    applyFixesBtn.classList.remove('hidden');
    // Reevaluate button only makes sense in review stage
    reevaluateBtn.classList.remove('hidden');
    recheckBtn.classList.remove('hidden');
  }

  reviewBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    reviewBtn.classList.add('hidden');
    progress.classList.remove('hidden');
    progressText.textContent = 'Scraping current values...';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const enriched = await chrome.runtime.sendMessage({ action: 'scrapeReview', tabId: tab.id });
      if (!enriched || enriched.error) throw new Error(enriched?.error || 'Scrape failed');
      scrapeData = enriched;

      progressText.textContent = 'Sending to /review...';
      const api = await getApi();
      const model = await getModel();
      const r = await fetch(`${api}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...enriched, model }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.error || `HTTP ${r.status}`);
      }
      const s = await r.json();
      if (s.status === 'done') {
        progress.classList.add('hidden');
        renderReview(s);
        return;
      }
      progressText.textContent = 'Claude is reviewing...';
      pollReview(api, scrapeData.task_id);
    } catch (err) {
      progress.classList.add('hidden');
      reviewBtn.classList.remove('hidden');
      showStatus(err.message, 'error');
    }
  });

  async function pollReview(api, tid) {
    for (let i = 0; i < 240; i++) {
      await new Promise(r => setTimeout(r, 3000));
      if (scrapeData?.task_id !== tid) return;
      progressText.textContent = `Reviewing... ${i * 3}s`;
      try {
        const r = await fetch(`${api}/review/status/${tid}`);
        const s = await r.json();
        if (s.status === 'done') {
          progress.classList.add('hidden');
          renderReview(s);
          pageStatusText.textContent = 'Review ready';
          pageStatusDot.className = 'status-dot connected';
          return;
        }
        if (s.status === 'error') throw new Error(s.error || 'Review failed');
      } catch (err) {
        if (err.message !== 'Failed to fetch') {
          progress.classList.add('hidden');
          reviewBtn.classList.remove('hidden');
          showStatus(err.message, 'error');
          return;
        }
      }
    }
    progress.classList.add('hidden');
    reviewBtn.classList.remove('hidden');
    showStatus('Review timeout', 'error');
  }

  applyFixesBtn.addEventListener('click', async () => {
    applyFixesBtn.disabled = true;
    applyFixesBtn.textContent = 'Applying...';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

      // 1. Clear all current fields on the page
      const cr = await chrome.runtime.sendMessage({ action: 'clearFields', tabId: tab.id });
      if (cr?.error) throw new Error(cr.error);

      // 2. Build merged payload: original scraped values overlaid with fixes
      const orig = scrapeData?.current || {};
      const fixed = reviewFixes || {};
      const merged = {
        quality:       { ...(orig.quality || {}),       ...(fixed.quality || {}) },
        severity:      { ...(orig.severity || {}),      ...(fixed.severity || {}) },
        context_scope: { ...(orig.context_scope || {}), ...(fixed.context_scope || {}) },
        advanced:      { ...(orig.advanced || {}),      ...(fixed.advanced || {}) },
        quality_score: reviewMeta.quality_score,
        feedback_text: reviewMeta.feedback_text,
      };

      // 3. Refill the page with the merged result
      const r = await chrome.runtime.sendMessage({
        action: 'fillDeliverables', tabId: tab.id, data: merged,
      });
      if (r.error) throw new Error(r.error);
      showStatus(`Cleared ${cr.cleared}, filled ${r.filled} field(s)${r.errors.length ? '. Issues: ' + r.errors.join('; ') : ''}`,
                 r.errors.length ? 'info' : 'success');
    } catch (err) {
      showStatus(err.message, 'error');
    }
    applyFixesBtn.textContent = 'Apply Review Fixes';
    applyFixesBtn.disabled = false;
  });

  reevaluateBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    reevaluateBtn.disabled = true;
    reevaluateBtn.textContent = 'Reevaluating...';
    reviewCard.classList.add('hidden');
    applyFixesBtn.classList.add('hidden');
    progress.classList.remove('hidden');
    progressText.textContent = 'Re-scraping current values...';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const enriched = await chrome.runtime.sendMessage({ action: 'scrapeReview', tabId: tab.id });
      if (!enriched || enriched.error) throw new Error(enriched?.error || 'Scrape failed');
      scrapeData = enriched;

      progressText.textContent = 'Sanity-checking proposed fixes...';
      const api = await getApi();
      const model = await getModel();
      const r = await fetch(`${api}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...enriched, reevaluate: true, model }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.error || `HTTP ${r.status}`);
      }
      const s = await r.json();
      if (s.status === 'done') {
        progress.classList.add('hidden');
        renderReview(s);
      } else {
        progressText.textContent = 'Claude is re-reviewing...';
        pollReview(api, scrapeData.task_id);
      }
    } catch (err) {
      progress.classList.add('hidden');
      showStatus(err.message, 'error');
    }
    reevaluateBtn.textContent = 'Reevaluate Review';
    reevaluateBtn.disabled = false;
  });

  // ============ Recheck ============
  recheckBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    recheckBtn.disabled = true;
    recheckBtn.textContent = 'Running recheck...';
    progress.classList.remove('hidden');
    progressText.textContent = 'Starting recheck...';
    try {
      const api = await getApi();
      const model = await getModel();
      const r = await fetch(`${api}/recheck`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: scrapeData.task_id, model }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.error || `HTTP ${r.status}`);
      }
      const s = await r.json();
      if (s.status === 'done') {
        progress.classList.add('hidden');
        showRecheckResult(s);
      } else {
        progressText.textContent = 'Claude is rechecking...';
        pollRecheck(api, scrapeData.task_id);
      }
    } catch (err) {
      progress.classList.add('hidden');
      showStatus(err.message, 'error');
    }
    recheckBtn.textContent = 'Recheck';
    recheckBtn.disabled = false;
  });

  async function pollRecheck(api, tid) {
    for (let i = 0; i < 120; i++) {
      await new Promise(r => setTimeout(r, 3000));
      if (scrapeData?.task_id !== tid) return;
      progressText.textContent = `Rechecking... ${i * 3}s`;
      try {
        const r = await fetch(`${api}/recheck/status/${tid}`);
        const s = await r.json();
        if (s.status === 'done') {
          progress.classList.add('hidden');
          showRecheckResult(s);
          recheckBtn.textContent = 'Recheck';
          recheckBtn.disabled = false;
          return;
        }
        if (s.status === 'error') throw new Error(s.error || 'Recheck failed');
      } catch (err) {
        if (err.message !== 'Failed to fetch') {
          progress.classList.add('hidden');
          recheckBtn.textContent = 'Recheck';
          recheckBtn.disabled = false;
          showStatus(err.message, 'error');
          return;
        }
      }
    }
    progress.classList.add('hidden');
    recheckBtn.textContent = 'Recheck';
    recheckBtn.disabled = false;
    showStatus('Recheck timeout', 'error');
  }

  function showRecheckResult(s) {
    const passed = s.passed;
    const report = s.report || '(no report generated)';
    showStatus(passed ? 'Recheck PASSED' : 'Recheck FAILED', passed ? 'success' : 'error');
    statusBody.innerHTML =
      `<div class="deliv-title">${passed ? '✅' : '❌'} Recheck ${passed ? 'Passed' : 'Failed'}</div>` +
      `<details open><summary>recheck_report.md</summary>` +
      `<pre class="deliv-text" style="white-space:pre-wrap;">${escapeHtml(report)}</pre></details>`;
    statusCard.classList.remove('hidden');
  }

  // ============ Status panel ============
  statusBtn.addEventListener('click', async () => {
    if (!scrapeData) return;
    statusBtn.disabled = true;
    statusBtn.textContent = 'Loading...';
    try {
      const api = await getApi();
      const r = await fetch(`${api}/state/${scrapeData.task_id}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const s = await r.json();
      renderStatus(s);
    } catch (err) {
      showStatus(err.message, 'error');
    }
    statusBtn.textContent = 'Status';
    statusBtn.disabled = false;
  });

  function renderStatus(s) {
    const dot = st => {
      const map = { done: '#22c55e', running: '#eab308', incomplete: '#f97316', error: '#ef4444', not_found: '#64748b' };
      return `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${map[st] || '#64748b'};margin-right:6px;"></span>`;
    };
    function block(title, b) {
      const head = `<div class="deliv-title">${dot(b.status)}${title}: <b>${b.status}</b></div>`;
      const err  = b.error ? `<div class="deliv-text" style="color:#ef4444;">${escapeHtml(b.error)}</div>` : '';
      const prog = b.progress
        ? `<details><summary>progress.md</summary><pre class="deliv-text" style="white-space:pre-wrap;">${escapeHtml(b.progress)}</pre></details>`
        : `<div class="deliv-text">(no progress file)</div>`;
      return `<div class="deliv">${head}${err}${prog}</div>`;
    }
    statusBody.innerHTML = block('Run pipeline', s.run || {status:'not_found'}) + block('Review', s.review || {status:'not_found'});
    statusCard.classList.remove('hidden');
  }

  // ============ Clear page fields ============
  clearBtn.addEventListener('click', async () => {
    clearBtn.disabled = true;
    clearBtn.textContent = 'Clearing...';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const r = await chrome.runtime.sendMessage({ action: 'clearFields', tabId: tab.id });
      if (r?.error) throw new Error(r.error);
      showStatus(`Cleared ${r.cleared} field(s)`, 'success');
    } catch (err) {
      showStatus(err.message, 'error');
    }
    clearBtn.textContent = 'Clear Page Fields';
    clearBtn.disabled = false;
  });
});
