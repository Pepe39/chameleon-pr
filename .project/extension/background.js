// Background service worker: routes scrape/fill requests to the active tab.

chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === 'scrapeTask') {
    chrome.scripting
      .executeScript({ target: { tabId: msg.tabId }, func: scrapeTaskPage })
      .then(([r]) => sendResponse(r.result))
      .catch(e => sendResponse({ error: e.message }));
    return true;
  }
  if (msg.action === 'fillDeliverables') {
    chrome.scripting
      .executeScript({
        target: { tabId: msg.tabId },
        func: fillDeliverablesPage,
        args: [msg.data]
      })
      .then(([r]) => sendResponse(r.result))
      .catch(e => sendResponse({ error: e.message }));
    return true;
  }
});

// =========================================================
// INJECTED: Scrape task inputs from the annotation platform
// =========================================================
function scrapeTaskPage() {
  try {
    const VARS = [
      'pull_request_url', 'nwo', 'head_sha', 'comment_id', 'body',
      'file_path', 'diff_line', 'discussion_url', 'repo_url', 'coding_language'
    ];

    // Heuristic: walk every element, look for one whose textContent matches a
    // variable name exactly, then read the closest "value" sibling/descendant.
    function normalize(s) { return (s || '').trim().toLowerCase(); }

    function findValueFor(varName) {
      const target = varName.toLowerCase();
      // 1. Look for elements whose text == varName (label-style)
      const candidates = document.querySelectorAll(
        'label, dt, th, span, div, strong, b, p, td'
      );
      for (const el of candidates) {
        if (normalize(el.textContent) !== target) continue;

        // Try sibling, then parent's next sibling, then parent's last child
        const tries = [
          el.nextElementSibling,
          el.parentElement?.nextElementSibling,
          el.parentElement?.querySelector('input, textarea, code, pre, a, dd, td:last-child, span:last-child')
        ];
        for (const t of tries) {
          if (!t) continue;
          if (t === el) continue;
          if (t.tagName === 'A' && t.href) return t.href;
          if (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA') return t.value || '';
          const txt = (t.innerText || t.textContent || '').trim();
          if (txt && normalize(txt) !== target) return txt;
        }
      }

      // 2. Fallback: data attributes / id matches
      const byAttr = document.querySelector(
        `[data-field="${varName}"], [data-name="${varName}"], [name="${varName}"], #${varName}`
      );
      if (byAttr) {
        if (byAttr.tagName === 'A') return byAttr.href || byAttr.textContent.trim();
        if ('value' in byAttr && byAttr.value) return byAttr.value;
        return (byAttr.innerText || byAttr.textContent || '').trim();
      }
      return '';
    }

    const data = {};
    for (const v of VARS) data[v] = findValueFor(v);

    // Extract task_id from URL: /tasks/{id}
    const m = location.pathname.match(/\/tasks\/([a-z0-9]+)/i);
    data.task_id = m ? m[1] : '';

    if (!data.task_id) return { error: 'Could not extract task_id from URL' };

    const missing = VARS.filter(v => !data[v]);
    data._missing = missing;
    return data;
  } catch (err) {
    return { error: err.message };
  }
}

// =========================================================
// INJECTED: Fill deliverables (4 axes) back into the platform
// =========================================================
function fillDeliverablesPage(deliverables) {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const results = { filled: 0, errors: [] };

  function findSection(title) {
    const headings = document.querySelectorAll('h1,h2,h3,h4,legend,label,div,span');
    for (const h of headings) {
      const t = (h.textContent || '').trim();
      if (t.startsWith(title)) {
        return h.closest('section, fieldset, form, div') || h.parentElement;
      }
    }
    return null;
  }

  async function clickRadio(section, value) {
    if (!section) return false;
    const radios = section.querySelectorAll('input[type="radio"], [role="radio"], button');
    for (const r of radios) {
      const label =
        r.getAttribute('aria-label') ||
        r.value ||
        r.textContent ||
        r.closest('label')?.textContent ||
        '';
      if (label.trim().toLowerCase() === value.trim().toLowerCase()) {
        r.click();
        await delay(80);
        return true;
      }
    }
    return false;
  }

  async function setTextarea(section, value) {
    if (!section) return false;
    const ta = section.querySelector('textarea, [contenteditable="true"]');
    if (!ta) return false;
    ta.focus();
    if (ta.tagName === 'TEXTAREA') {
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, value);
    } else {
      ta.textContent = value;
    }
    ta.dispatchEvent(new Event('input', { bubbles: true }));
    ta.dispatchEvent(new Event('change', { bubbles: true }));
    ta.blur();
    await delay(80);
    return true;
  }

  async function fillAxis(axisTitle, label, justification) {
    const section = findSection(axisTitle);
    if (!section) { results.errors.push(`${axisTitle} section not found`); return; }
    if (await clickRadio(section, label)) results.filled++;
    else results.errors.push(`${axisTitle}: label "${label}" not found`);

    const justSection =
      findSection(`${axisTitle} Justification`) ||
      findSection(`${axisTitle.replace(':', '')} Justification`) ||
      section;
    if (await setTextarea(justSection, justification)) results.filled++;
    else results.errors.push(`${axisTitle}: justification textarea not found`);
  }

  async function fillContextEntries(entries) {
    // Best-effort: find the context table and fill rows
    const tables = document.querySelectorAll('table, [role="table"]');
    let table = null;
    for (const t of tables) {
      if ((t.textContent || '').includes('diff_line') &&
          (t.textContent || '').includes('file_path')) {
        table = t; break;
      }
    }
    if (!table) { results.errors.push('Context table not found'); return; }

    for (let i = 0; i < entries.length; i++) {
      const e = entries[i];
      // The platform usually has an "Add row" button
      const addBtn = Array.from(document.querySelectorAll('button')).find(
        b => /add row|\+/i.test(b.textContent || '')
      );
      if (i > 0 && addBtn) { addBtn.click(); await delay(120); }

      const rows = table.querySelectorAll('tr, [role="row"]');
      const row = rows[i + 1] || rows[rows.length - 1];
      if (!row) continue;
      const inputs = row.querySelectorAll('input, textarea, [contenteditable="true"]');
      const values = [e.diff_line || '', e.file_path || '', e.why || ''];
      for (let k = 0; k < Math.min(inputs.length, values.length); k++) {
        const el = inputs[k];
        el.focus();
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
          const proto = el.tagName === 'INPUT' ? HTMLInputElement.prototype : HTMLTextAreaElement.prototype;
          const setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
          setter.call(el, values[k]);
        } else {
          el.textContent = values[k];
        }
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
        el.blur();
        await delay(60);
      }
      results.filled++;
    }
  }

  async function run() {
    const q = deliverables.quality || {};
    const s = deliverables.severity || {};
    const c = deliverables.context_scope || {};
    const a = deliverables.advanced || {};

    await fillAxis('Axis 1: Quality', q.label || '', q.reasoning || '');
    await fillAxis('Axis 2: Severity', s.label || '', s.reasoning || '');

    // Axis 3: label + entries
    const ctxSection = findSection('Axis 3: Context');
    if (ctxSection && c.label) {
      if (await clickRadio(ctxSection, c.label)) results.filled++;
      else results.errors.push(`Axis 3: label "${c.label}" not found`);
    }
    if (Array.isArray(c.entries) && c.entries.length) {
      await fillContextEntries(c.entries);
    }

    await fillAxis('Axis 4: Advanced', a.label || '', a.reasoning || '');

    return results;
  }

  return run();
}
