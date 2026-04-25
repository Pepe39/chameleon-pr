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
  if (msg.action === 'scrapeReview') {
    chrome.scripting
      .executeScript({ target: { tabId: msg.tabId }, func: scrapeReviewPage })
      .then(([r]) => sendResponse(r.result))
      .catch(e => sendResponse({ error: e.message }));
    return true;
  }
  if (msg.action === 'clearFields') {
    chrome.scripting
      .executeScript({ target: { tabId: msg.tabId }, func: clearFieldsPage })
      .then(([r]) => sendResponse(r.result))
      .catch(e => sendResponse({ error: e.message }));
    return true;
  }
});

// =========================================================
// INJECTED: Scrape a New Review page (variables + current axis values)
// =========================================================
function scrapeReviewPage() {
  try {
    const VARS = ['pull_request_url','nwo','head_sha','comment_id','body','file_path','diff_line','discussion_url','repo_url','coding_language'];
    function normalize(s){return (s||'').trim().toLowerCase();}
    function findValueFor(v){
      const target=v.toLowerCase(), tc=target+':';
      const all=document.querySelectorAll('label, dt, th, span, div, strong, b, p, td');
      for (const el of all){
        const t=normalize(el.textContent);
        if (t!==target && t!==tc) continue;
        const tries=[el.nextElementSibling,
                     el.parentElement?.lastElementChild!==el?el.parentElement?.lastElementChild:null,
                     el.parentElement?.nextElementSibling];
        for (const c of tries){
          if(!c||c===el) continue;
          if(c.tagName==='A'&&c.href) return c.href;
          if(c.tagName==='INPUT'||c.tagName==='TEXTAREA') return c.value||'';
          const txt=(c.innerText||c.textContent||'').trim();
          if(txt && normalize(txt)!==target && normalize(txt)!==tc) return txt;
        }
      }
      return '';
    }

    const data = {};
    for (const v of VARS) data[v] = findValueFor(v);
    const m = location.pathname.match(/\/tasks\/([a-z0-9]+)/i);
    data.task_id = m ? m[1] : '';
    if (!data.task_id) return { error: 'Could not extract task_id from URL' };

    // Find the tight section around an axis label and return select + nearest justification textarea
    function tightSection(title) {
      const labels = document.querySelectorAll('label, h1, h2, h3, h4, legend');
      for (const h of labels) {
        if (!(h.textContent || '').trim().startsWith(title)) continue;
        let p = h.parentElement;
        for (let i = 0; i < 12 && p; i++) {
          const ctrls = p.querySelectorAll('select, textarea').length;
          const axes = (p.textContent || '').match(/Axis \d/g) || [];
          if (ctrls >= 1 && axes.length <= 1) return p;
          p = p.parentElement;
        }
      }
      return null;
    }
    function justFor(title) {
      // Justification is in a sibling section with title "{title} Justification"
      const sec = tightSection(`${title} Justification`);
      const ta = sec?.querySelector('textarea');
      return ta?.value || '';
    }
    function selVal(title) {
      const sec = tightSection(title);
      const sel = sec?.querySelector('select');
      return sel?.value || '';
    }

    const current = {
      quality:       { label: selVal('Axis 1: Quality'),   reasoning: justFor('Axis 1: Quality') },
      addressed:     { label: selVal('Axis 2: Addressed'), reasoning: justFor('Axis 2: Addressed') },
      severity:      { label: selVal('Axis 3: Severity'),  reasoning: justFor('Axis 3: Severity') },
      context_scope: { label: selVal('Axis 4: Context'),   entries: [] },
      advanced:      { label: selVal('Axis 5: Advanced'),  reasoning: justFor('Axis 5: Advanced') },
    };
    // Drop the Addressed block if the platform did not render it (open PRs omit the section).
    if (!current.addressed.label && !current.addressed.reasoning) {
      delete current.addressed;
    }

    // Context entries from the table
    const tbl = Array.from(document.querySelectorAll('table'))
      .find(t => /diff_line/.test(t.textContent || '') && /file_path/.test(t.textContent || ''));
    if (tbl) {
      const tbody = tbl.querySelector('tbody') || tbl;
      tbody.querySelectorAll('tr').forEach(tr => {
        const fields = tr.querySelectorAll('input, textarea');
        if (fields.length >= 3) {
          const dl = fields[0].value || '';
          const fp = fields[1].value || '';
          const wy = fields[2].value || '';
          // Skip the platform's blank placeholder row.
          if (!dl.trim() && !fp.trim() && !wy.trim()) return;
          current.context_scope.entries.push({
            diff_line: dl,
            file_path: fp,
            why: wy,
          });
        }
      });
    }

    return { ...data, current };
  } catch (err) {
    return { error: err.message };
  }
}

// =========================================================
// INJECTED: Clear all axis fields on the annotation platform
// =========================================================
function clearFieldsPage() {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  let cleared = 0;

  function fire(el, ev) {
    el.dispatchEvent(new Event(ev, { bubbles: true }));
  }

  return (async () => {
    // 1. Reset every <select> to its first option (the "— Select —" placeholder)
    document.querySelectorAll('select').forEach(s => {
      if (!s.options.length) return;
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
      setter.call(s, s.options[0].value);
      fire(s, 'input'); fire(s, 'change');
      cleared++;
    });

    // 2. Empty every textarea EXCEPT the global comment box and a stray "Add a comment" field
    document.querySelectorAll('textarea').forEach(t => {
      const ph = (t.placeholder || '').toLowerCase();
      // Skip the discussion comment box at the bottom of the page
      if (ph.includes('add a comment') || ph.includes('mention')) return;
      if (!t.value && !t.textContent) return;
      const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
      setter.call(t, '');
      fire(t, 'input'); fire(t, 'change');
      cleared++;
    });

    // 3. Remove all rows from the Context Evidence table by clicking each row's delete button
    const tables = document.querySelectorAll('table, [role="table"]');
    let ctxTable = null;
    for (const t of tables) {
      const txt = t.textContent || '';
      if (txt.includes('diff_line') && txt.includes('file_path') && txt.includes('why')) {
        ctxTable = t; break;
      }
    }
    if (ctxTable) {
      // Loop until no data rows remain. Each iteration: find the last data row, click its delete button.
      for (let safety = 0; safety < 50; safety++) {
        const tbody = ctxTable.querySelector('tbody') || ctxTable;
        const dataRows = Array.from(tbody.querySelectorAll('tr')).filter(r =>
          r.querySelectorAll('input, textarea, [contenteditable="true"]').length > 0
        );
        if (!dataRows.length) break;
        const row = dataRows[dataRows.length - 1];
        // Try common delete affordances
        const delBtn =
          row.querySelector('button[aria-label*="delete" i], button[aria-label*="remove" i], button[title*="delete" i], button[title*="remove" i]') ||
          Array.from(row.querySelectorAll('button')).find(b => /^(×|x|delete|remove|trash|🗑)$/i.test((b.textContent || '').trim()));
        if (!delBtn) break;
        delBtn.click();
        await delay(80);
        cleared++;
      }
    }

    return { cleared };
  })();
}

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
      const targetColon = target + ':';
      // 1. Look for label elements whose text == "varName" or "varName:"
      const candidates = document.querySelectorAll(
        'label, dt, th, span, div, strong, b, p, td'
      );
      for (const el of candidates) {
        const t = normalize(el.textContent);
        if (t !== target && t !== targetColon) continue;

        // Prefer the label's next sibling (the value element)
        const tries = [
          el.nextElementSibling,
          el.parentElement?.lastElementChild !== el ? el.parentElement?.lastElementChild : null,
          el.parentElement?.nextElementSibling,
        ];
        for (const cand of tries) {
          if (!cand || cand === el) continue;
          if (cand.tagName === 'A' && cand.href) return cand.href;
          if (cand.tagName === 'INPUT' || cand.tagName === 'TEXTAREA') return cand.value || '';
          const txt = (cand.innerText || cand.textContent || '').trim();
          if (txt && normalize(txt) !== target && normalize(txt) !== targetColon) return txt;
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
// INJECTED: Fill deliverables (5 axes) back into the platform
// Axis 2 Addressed is only filled on merged PRs, the platform hides the
// section on open PRs and the pipeline omits the `addressed` key.
// =========================================================
function fillDeliverablesPage(deliverables) {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const results = { filled: 0, errors: [] };

  // Find the tightest container around a heading/label that holds a form control.
  // Walks up from a label whose text starts with `title` until the parent contains
  // at least one of the wanted control types AND no more than one Axis heading.
  // Wanted selector includes custom dropdowns (button-based comboboxes used by
  // some annotation-hub form components) in addition to native form controls.
  function findSection(title, wantedSelector = 'select, textarea, input[type="radio"], [role="radio"], button[aria-haspopup="listbox"], [role="combobox"]') {
    const norm = s => (s || '').trim();
    const candidates = document.querySelectorAll('label, h1, h2, h3, h4, legend');
    for (const h of candidates) {
      if (!norm(h.textContent).startsWith(title)) continue;
      let p = h.parentElement;
      for (let i = 0; i < 12 && p; i++) {
        const ctrls = p.querySelectorAll(wantedSelector).length;
        const axisMentions = (p.textContent || '').match(/Axis \d/g) || [];
        if (ctrls >= 1 && axisMentions.length <= 1) return p;
        p = p.parentElement;
      }
    }
    return null;
  }

  // Try multiple candidate titles in order. Returns the first section found.
  // Used for axes whose label text varies between Annotation stage and Review
  // stage, or between platform versions.
  function findSectionAny(titles, wantedSelector) {
    for (const t of titles) {
      const s = findSection(t, wantedSelector);
      if (s) return s;
    }
    return null;
  }

  // For diagnostic logging when a section is found but no control inside it
  // matched the desired value. Lists every control text/value/aria-label so
  // we can tell what the platform is actually rendering.
  function dumpSectionControls(section) {
    const controls = section.querySelectorAll('select, input, button, [role="radio"], [role="combobox"], [aria-haspopup]');
    return Array.from(controls).slice(0, 20).map(c => ({
      tag: c.tagName,
      type: c.getAttribute('type'),
      role: c.getAttribute('role'),
      ariaLabel: c.getAttribute('aria-label'),
      text: (c.textContent || '').trim().slice(0, 40),
      value: c.value,
    }));
  }

  async function clickRadio(section, value) {
    if (!section) return false;
    const want = value.trim().toLowerCase();
    const wantNorm = want.replace(/\s+/g, ' ');

    // 1. Native <select> dropdown
    const select = section.querySelector('select');
    if (select) {
      const opt = Array.from(select.options).find(o =>
        (o.value || '').trim().toLowerCase() === want ||
        (o.textContent || '').trim().toLowerCase() === want
      );
      if (opt) {
        const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set;
        setter.call(select, opt.value);
        select.dispatchEvent(new Event('input', { bubbles: true }));
        select.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(80);
        return true;
      }
    }

    // 2. Custom combobox (Radix UI, Headless UI, etc). The trigger button
    // exposes role="combobox" or aria-haspopup="listbox". Options live in a
    // separate listbox that opens on click and is often portaled to <body>.
    const combo = section.querySelector('button[aria-haspopup="listbox"], [role="combobox"]');
    if (combo) {
      combo.click();
      await delay(180);
      // Options can be portaled outside the section, search the whole document
      const options = Array.from(document.querySelectorAll('[role="option"]'));
      for (const o of options) {
        const text = ((o.getAttribute('aria-label') || '') + ' ' + (o.textContent || ''))
          .trim().toLowerCase().replace(/\s+/g, ' ');
        if (text === wantNorm || text.startsWith(wantNorm + ' ') || text.startsWith(wantNorm + ',')) {
          o.click();
          await delay(120);
          return true;
        }
      }
      // No exact-prefix match, log what options were available before closing
      const dump = options.slice(0, 12).map(o => ({
        ariaLabel: o.getAttribute('aria-label'),
        text: (o.textContent || '').trim().slice(0, 40),
      }));
      console.error('[code-review] Combobox open but no [role=option] matched ' + JSON.stringify(want) + '. Options seen: ' + JSON.stringify(dump));
      // Close the menu by clicking trigger again
      combo.click();
      await delay(80);
    }

    // 3. Radios / role=radio / buttons within the section
    const radios = section.querySelectorAll('input[type="radio"], [role="radio"], button');
    for (const r of radios) {
      const label =
        r.getAttribute('aria-label') ||
        r.value ||
        r.textContent ||
        r.closest('label')?.textContent ||
        '';
      const norm = label.trim().toLowerCase().replace(/\s+/g, ' ');
      if (norm === wantNorm) {
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
    console.log('[code-review] fillContextEntries v0.1.1 starting, entries=', entries.length);
    const tables = document.querySelectorAll('table, [role="table"]');
    let table = null;
    for (const t of tables) {
      if ((t.textContent || '').includes('diff_line') &&
          (t.textContent || '').includes('file_path')) {
        table = t; break;
      }
    }
    if (!table) { results.errors.push('Context table not found'); return; }

    const addBtn = Array.from(document.querySelectorAll('button')).find(
      b => /^\s*add row\s*$/i.test(b.textContent || '')
    );
    if (!addBtn) { results.errors.push('Add Row button not found'); return; }

    // Count existing data rows (skip "No rows yet" placeholder)
    function dataRows() {
      const tbody = table.querySelector('tbody') || table;
      return Array.from(tbody.querySelectorAll('tr')).filter(r =>
        r.querySelectorAll('input, textarea, [contenteditable="true"]').length > 0
      );
    }

    // Drop entries where all three fields are empty. These come from the
    // platform's blank placeholder row being picked up during scrape, and
    // refilling them would re-introduce the validation error we're fixing.
    const nonEmpty = entries.filter(e =>
      (e.diff_line || '').trim() || (e.file_path || '').trim() || (e.why || '').trim()
    );
    function rowIsEmpty(r) {
      const flds = r.querySelectorAll('input, textarea, [contenteditable="true"]');
      return Array.from(flds).every(f =>
        !(((f.value != null ? f.value : f.textContent) || '').trim())
      );
    }

    for (let i = 0; i < nonEmpty.length; i++) {
      const e = nonEmpty[i];

      // Reuse an existing empty row if one survived clearFields. Some
      // platform placeholder rows have no delete button, so clearFields
      // cannot remove them. Filling them avoids leaving a blank row that
      // trips the context-entries-have-file-path/why validators.
      let row = dataRows().find(rowIsEmpty) || null;
      if (!row) {
        const before = dataRows().length;
        addBtn.click();
        for (let w = 0; w < 20 && dataRows().length === before; w++) await delay(50);
        const rows = dataRows();
        row = rows[rows.length - 1];
      }
      if (!row) { results.errors.push(`Context row ${i + 1} not created`); continue; }

      const fields = row.querySelectorAll('input, textarea, [contenteditable="true"]');
      const values = [e.diff_line || '', e.file_path || '', e.why || ''];
      for (let k = 0; k < Math.min(fields.length, values.length); k++) {
        const el = fields[k];
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

    // Final sweep: try to delete any row that ended up empty. Some platform
    // placeholder rows have no delete button, in which case we log and move on.
    for (let safety = 0; safety < 20; safety++) {
      const stray = dataRows().find(rowIsEmpty);
      if (!stray) break;
      const delBtn =
        stray.querySelector('button[aria-label*="delete" i], button[aria-label*="remove" i], button[title*="delete" i], button[title*="remove" i]') ||
        Array.from(stray.querySelectorAll('button')).find(b => /^(×|x|delete|remove|trash|🗑)$/i.test((b.textContent || '').trim()));
      if (!delBtn) {
        console.warn('[code-review] empty row has no delete button, cannot remove');
        results.errors.push('empty context row could not be removed');
        break;
      }
      delBtn.click();
      await delay(100);
    }
  }

  async function run() {
    const q  = deliverables.quality || {};
    const ad = deliverables.addressed || null;
    const s  = deliverables.severity || {};
    const c  = deliverables.context_scope || {};
    const a  = deliverables.advanced || {};

    await fillAxis('Axis 1: Quality', q.label || '', q.reasoning || '');

    // Axis 2: Addressed is only filled when the PR was merged. For open PRs,
    // the API omits the `addressed` key and the platform hides the section.
    if (ad && ad.label && findSection('Axis 2: Addressed')) {
      await fillAxis('Axis 2: Addressed', ad.label || '', ad.reasoning || '');
    }

    await fillAxis('Axis 3: Severity', s.label || '', s.reasoning || '');

    // Axis 4: Context label + entries. Try multiple title variants because
    // some Annotation-stage forms render the label as "Axis 4: Context Scope"
    // while Review-stage forms use the shorter "Axis 4: Context". Pre-Addressed
    // tasks may still surface as "Axis 3: Context Scope".
    const ctxSection = findSectionAny([
      'Axis 4: Context Scope',
      'Axis 4: Context',
      'Axis 3: Context Scope',
    ]);
    if (!ctxSection) {
      console.error('[code-review] Context Scope section not found. Tried Axis 4: Context Scope, Axis 4: Context, Axis 3: Context Scope');
      results.errors.push('Context Scope section not found, tried Axis 4: Context Scope / Axis 4: Context / Axis 3: Context Scope');
    } else if (c.label) {
      if (await clickRadio(ctxSection, c.label)) {
        results.filled++;
      } else {
        const dump = dumpSectionControls(ctxSection);
        console.error('[code-review] Context Scope label not selectable. label=' + JSON.stringify(c.label) + ' controls=' + JSON.stringify(dump));
        results.errors.push(`Context Scope label "${c.label}" not selectable in section. Open dev tools console for control dump`);
      }
    }
    if (Array.isArray(c.entries) && c.entries.length) {
      await fillContextEntries(c.entries);
    }

    await fillAxis('Axis 5: Advanced', a.label || '', a.reasoning || '');

    // Quality Score: 1-5 star buttons under "Quality Score" label
    if (deliverables.quality_score) {
      const n = parseInt(deliverables.quality_score, 10);
      if (n >= 1 && n <= 5) {
        const labels = document.querySelectorAll('label, h1, h2, h3, h4, legend');
        let scoreLabel = null;
        for (const l of labels) {
          if (/Quality Score/i.test(l.textContent || '')) { scoreLabel = l; break; }
        }
        if (scoreLabel) {
          const container = scoreLabel.parentElement;
          const starBtn = container?.querySelector(`button[aria-label="${n} star"], button[aria-label="${n} stars"]`);
          if (starBtn) { starBtn.click(); await delay(80); results.filled++; }
          else results.errors.push(`Quality Score button for ${n} not found`);
        } else {
          results.errors.push('Quality Score label not found');
        }
      }
    }

    // Feedback textarea: <textarea placeholder="Add feedback for the attempter...">
    if (deliverables.feedback_text) {
      const fbTa = Array.from(document.querySelectorAll('textarea'))
        .find(t => /add feedback for the attempter/i.test(t.placeholder || ''));
      if (fbTa) {
        const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
        setter.call(fbTa, deliverables.feedback_text);
        fbTa.dispatchEvent(new Event('input', { bubbles: true }));
        fbTa.dispatchEvent(new Event('change', { bubbles: true }));
        await delay(80);
        results.filled++;
      } else {
        results.errors.push('Feedback textarea not found');
      }
    }

    return results;
  }

  return run();
}
