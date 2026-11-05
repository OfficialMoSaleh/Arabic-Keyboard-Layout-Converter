// Content Script - Smart Movable In-Field Badge
(function () {
  'use strict';

  if (window.__arabicKeyConverterUltraV6) return;
  window.__arabicKeyConverterUltraV6 = true;

  if (document.contentType && !/html/i.test(document.contentType)) return;
  if (!document.documentElement || typeof KeyConverter === 'undefined') return;

  const HOST_ID = 'arabic-converter-extension-root';

  // Remove any previous host if present
  const oldHost = document.getElementById(HOST_ID);
  if (oldHost) oldHost.remove();

  // Create clean shadow host - Simple bulletproof fixed container
  const host = document.createElement('div');
  host.id = HOST_ID;
  host.style.cssText = 'all:initial;position:fixed;top:0;left:0;width:0;height:0;z-index:2147483647;pointer-events:none;overflow:visible;';
  
  function ensureHostInDOM() {
    if (!document.documentElement.contains(host)) {
      (document.body || document.documentElement).appendChild(host);
    }
  }
  ensureHostInDOM();

  const shadow = host.attachShadow({ mode: 'open' });

  // Styles
  const style = document.createElement('style');
  style.textContent = `
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      user-select: none;
      -webkit-user-select: none;
    }

    /* Smart Movable In-Field Badge - Only ONE badge on screen! */
    .field-badge {
      position: fixed;
      display: none;
      align-items: center;
      gap: 6px;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1.5px solid rgba(59, 130, 246, 0.75);
      border-radius: 20px;
      padding: 4px 8px 4px 10px;
      color: #f8fafc;
      font: 700 12px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      cursor: pointer;
      pointer-events: auto !important;
      direction: rtl;
      box-shadow: 0 10px 28px rgba(0, 0, 0, 0.5), 0 0 16px rgba(59, 130, 246, 0.35);
      z-index: 2147483647;
      white-space: nowrap;
      touch-action: none;
      opacity: 0;
      transform: scale(0.92);
      transition: opacity 0.15s ease, transform 0.15s ease, border-color 0.2s, box-shadow 0.2s;
    }

    .field-badge.visible {
      display: flex;
      opacity: 1;
      transform: scale(1);
    }

    .field-badge.dragging {
      cursor: grabbing !important;
      transition: none !important;
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.7), 0 0 25px rgba(59, 130, 246, 0.6);
      border-color: #60a5fa;
      transform: scale(1.05) !important;
    }

    .field-badge:hover:not(.dragging) {
      border-color: #60a5fa;
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6), 0 0 20px rgba(59, 130, 246, 0.5);
      transform: translateY(-1px);
    }

    /* Drag Handle Grip */
    .field-badge .badge-grip {
      color: #64748b;
      padding: 2px 4px;
      font-size: 14px;
      cursor: grab;
      display: flex;
      align-items: center;
      transition: color 0.15s;
    }

    .field-badge .badge-grip:hover {
      color: #94a3b8;
    }

    /* Main Action Button inside Badge */
    .field-badge .badge-main {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 2px 6px;
      border-radius: 12px;
      cursor: pointer;
      transition: background 0.15s;
    }

    .field-badge .badge-main:hover {
      background: rgba(37, 99, 235, 0.25);
    }

    .field-badge .badge-icon {
      font-size: 14px;
      display: inline-block;
      transition: transform 0.3s ease;
    }

    .field-badge:hover .badge-icon {
      transform: rotate(180deg);
    }

    .field-badge .badge-text {
      font-weight: 700;
      color: #f8fafc;
    }

    .field-badge .badge-sub {
      font-size: 10px;
      color: #38bdf8;
      font-weight: 600;
      background: rgba(56, 189, 248, 0.12);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: 8px;
      padding: 1px 5px;
    }

    /* Close Button */
    .field-badge .badge-close {
      width: 18px;
      height: 18px;
      display: flex;
      align-items: center;
      justify-content: center;
      border: none;
      background: transparent;
      color: #64748b;
      border-radius: 50%;
      font-size: 13px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.15s;
      margin-right: 2px;
    }

    .field-badge .badge-close:hover {
      background: rgba(239, 68, 68, 0.2);
      color: #f87171;
    }

    /* Toast Notification */
    .toast {
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%) translateY(-10px);
      background: #0f172a;
      color: #f8fafc;
      border: 1.5px solid #3b82f6;
      border-radius: 25px;
      padding: 9px 20px;
      font: 600 13px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      display: none;
      align-items: center;
      gap: 8px;
      direction: rtl;
      box-shadow: 0 12px 35px rgba(0,0,0,0.6);
      pointer-events: none;
      z-index: 2147483647;
      opacity: 0;
      transition: opacity 0.25s ease, transform 0.25s ease;
    }

    .toast.active {
      display: flex;
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
  `;
  shadow.appendChild(style);

  // --- Movable In-Field Badge ---
  const fieldBadge = document.createElement('div');
  fieldBadge.className = 'field-badge';
  fieldBadge.innerHTML = `
    <span class="badge-grip" title="اسحب لتحريك البوبوب في أي مكان">⋮⋮</span>
    <div class="badge-main" role="button" title="انقر للتحويل الفوري (أو اضغط Ctrl+Shift+X)">
      <span class="badge-icon">🔄</span>
      <span class="badge-text">تحويل</span>
      <span class="badge-sub">عربي ⇋ En</span>
    </div>
    <button class="badge-close" title="إخفاء مؤقت لهذا الحقل">✕</button>
  `;
  shadow.appendChild(fieldBadge);

  // --- Toast ---
  const toast = document.createElement('div');
  toast.className = 'toast';
  shadow.appendChild(toast);

  let toastTimeout = null;
  function showToast(msg, isSuccess = true) {
    toast.textContent = msg;
    toast.style.borderColor = isSuccess ? '#3b82f6' : '#ef4444';
    toast.classList.add('active');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.remove('active'), 2000);
  }

  // ---------------------------------------------------------------------------
  // Target Detection
  // ---------------------------------------------------------------------------
  let currentTargetEl = null;
  let dismissedEl = null;
  let userBadgePos = null; // { left, top } custom drag position
  let showBadgeEnabled = true;

  // Load setting
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get({ showFieldBadge: true }, (res) => {
      showBadgeEnabled = res.showFieldBadge !== false;
      if (!showBadgeEnabled) hideBadge();
    });
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.showFieldBadge) {
        showBadgeEnabled = changes.showFieldBadge.newValue !== false;
        if (!showBadgeEnabled) hideBadge();
        else if (currentTargetEl) repositionFieldBadge(currentTargetEl);
      }
    });
  }

  function getEditable(el) {
    if (!el || el.nodeType !== 1) return null;

    // 1. Direct or ancestor input / textarea
    const input = el.closest ? el.closest('input, textarea') : (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' ? el : null);
    if (input) {
      if (input.disabled || input.readOnly) return null;
      if (input.tagName === 'INPUT') {
        const type = (input.type || 'text').toLowerCase();
        const nonText = ['password', 'checkbox', 'radio', 'file', 'submit', 'button', 'image', 'reset', 'range', 'color'];
        if (nonText.includes(type)) return null;
      }
      return input;
    }

    // 2. Direct or ancestor contenteditable (WhatsApp Web, ChatGPT, Facebook, Notion, Twitter/X, Gmail, Slack, etc.)
    if (el.isContentEditable) {
      let hostEl = el;
      while (hostEl.parentElement && hostEl.parentElement.isContentEditable) {
        hostEl = hostEl.parentElement;
      }
      return hostEl;
    }

    const ce = el.closest ? el.closest('[contenteditable="true"], [contenteditable=""], [contenteditable="plaintext-only"]') : null;
    if (ce && !ce.disabled && !ce.readOnly) return ce;

    // 3. Elements with role="textbox" or role="searchbox"
    const roleBox = el.closest ? el.closest('[role="textbox"], [role="searchbox"]') : null;
    if (roleBox) {
      const inner = roleBox.querySelector('input, textarea, [contenteditable="true"]');
      if (inner) return getEditable(inner);
      return roleBox;
    }

    return null;
  }

  function getEditableFromEvent(e) {
    const path = e.composedPath ? e.composedPath() : [];
    if (path.includes(host)) return null;
    for (const node of path) {
      if (node && node.nodeType === 1) {
        const ed = getEditable(node);
        if (ed) return ed;
      }
    }
    return getEditable(e.target);
  }

  function hideBadge() {
    fieldBadge.classList.remove('visible');
    fieldBadge.style.display = 'none';
  }

  function updateTarget(el) {
    if (!showBadgeEnabled) return;
    ensureHostInDOM();
    if (!el) return;
    if (el !== currentTargetEl) {
      currentTargetEl = el;
      userBadgePos = null; // reset drag position when moving to a new field
    }
    if (currentTargetEl === dismissedEl) return;
    repositionFieldBadge(el);
  }

  function repositionFieldBadge(el) {
    if (!showBadgeEnabled || !el || !document.contains(el)) return hideBadge();
    const rect = el.getBoundingClientRect();

    if (rect.width === 0 && rect.height === 0) return hideBadge();
    if (rect.bottom < 0 || rect.top > window.innerHeight || rect.right < 0 || rect.left > window.innerWidth) {
      return hideBadge();
    }

    fieldBadge.style.display = 'flex';
    fieldBadge.classList.add('visible');

    const w = fieldBadge.offsetWidth || 135;
    const h = fieldBadge.offsetHeight || 32;

    let left, top;

    // If user dragged it, keep their custom location:
    if (userBadgePos) {
      left = Math.max(4, Math.min(window.innerWidth - w - 4, userBadgePos.left));
      top = Math.max(4, Math.min(window.innerHeight - h - 4, userBadgePos.top));
    } else {
      // Smart Default Positioning: Right-aligned above the input
      left = rect.right - w;
      top = rect.top - h - 6;

      // If not enough room above, place just below
      if (top < 6) {
        top = rect.bottom + 6;
      }

      // Clamp inside viewport
      left = Math.max(6, Math.min(window.innerWidth - w - 6, left));
      top = Math.max(6, Math.min(window.innerHeight - h - 6, top));
    }

    fieldBadge.style.left = `${Math.round(left)}px`;
    fieldBadge.style.top = `${Math.round(top)}px`;
  }

  // ---------------------------------------------------------------------------
  // Dragging Mechanics for fieldBadge
  // ---------------------------------------------------------------------------
  let isDraggingBadge = false;
  let badgeDragData = null;

  fieldBadge.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    e.stopPropagation();

    // If close button clicked
    if (e.target.closest('.badge-close')) {
      hideBadge();
      dismissedEl = currentTargetEl;
      return;
    }

    isDraggingBadge = false;
    const r = fieldBadge.getBoundingClientRect();
    badgeDragData = {
      startX: e.clientX,
      startY: e.clientY,
      origLeft: r.left,
      origTop: r.top
    };

    const onPointerMove = (ev) => {
      if (!badgeDragData) return;
      const dx = ev.clientX - badgeDragData.startX;
      const dy = ev.clientY - badgeDragData.startY;
      if (!isDraggingBadge && Math.hypot(dx, dy) < 4) return;

      isDraggingBadge = true;
      fieldBadge.classList.add('dragging');

      let newLeft = badgeDragData.origLeft + dx;
      let newTop = badgeDragData.origTop + dy;

      const w = fieldBadge.offsetWidth || 135;
      const h = fieldBadge.offsetHeight || 32;
      newLeft = Math.max(4, Math.min(window.innerWidth - w - 4, newLeft));
      newTop = Math.max(4, Math.min(window.innerHeight - h - 4, newTop));

      fieldBadge.style.left = `${Math.round(newLeft)}px`;
      fieldBadge.style.top = `${Math.round(newTop)}px`;
    };

    const onPointerUp = (ev) => {
      document.removeEventListener('pointermove', onPointerMove, true);
      document.removeEventListener('pointerup', onPointerUp, true);
      document.removeEventListener('pointercancel', onPointerUp, true);

      fieldBadge.classList.remove('dragging');

      if (isDraggingBadge) {
        const r = fieldBadge.getBoundingClientRect();
        userBadgePos = { left: r.left, top: r.top };
        isDraggingBadge = false;
        return;
      }

      badgeDragData = null;

      // Pure click: execute conversion!
      executeConvert(true);
    };

    document.addEventListener('pointermove', onPointerMove, true);
    document.addEventListener('pointerup', onPointerUp, true);
    document.addEventListener('pointercancel', onPointerUp, true);
  });

  // ---------------------------------------------------------------------------
  // Listeners to detect user focusing/typing on ANY field
  // ---------------------------------------------------------------------------
  document.addEventListener('focusin', (e) => {
    const ed = getEditableFromEvent(e);
    if (ed) updateTarget(ed);
  }, true);

  document.addEventListener('pointerdown', (e) => {
    if (host.contains(e.target) || (e.composedPath && e.composedPath().includes(host))) return;

    const ed = getEditableFromEvent(e);
    if (ed) {
      updateTarget(ed);
    } else {
      setTimeout(() => {
        const active = getEditable(document.activeElement);
        if (!active) {
          hideBadge();
          currentTargetEl = null;
          userBadgePos = null;
        }
      }, 180);
    }
  }, true);

  document.addEventListener('input', (e) => {
    const ed = getEditableFromEvent(e);
    if (ed) updateTarget(ed);
  }, true);

  document.addEventListener('keyup', (e) => {
    const ed = getEditableFromEvent(e);
    if (ed) updateTarget(ed);
  }, true);

  window.addEventListener('scroll', () => {
    if (currentTargetEl) repositionFieldBadge(currentTargetEl);
  }, { passive: true, capture: true });

  window.addEventListener('resize', () => {
    if (currentTargetEl) repositionFieldBadge(currentTargetEl);
  }, { passive: true });

  // Initial check on load
  setTimeout(() => {
    const active = getEditable(document.activeElement);
    if (active) updateTarget(active);
  }, 300);

  // ---------------------------------------------------------------------------
  // Conversion Logic (Immediate conversion without requiring selection!)
  // ---------------------------------------------------------------------------
  function fireInputEvents(el, data) {
    let ev;
    try {
      ev = new InputEvent('input', { bubbles: true, inputType: 'insertText', data });
    } catch (e) {
      ev = new Event('input', { bubbles: true });
    }
    el.dispatchEvent(ev);
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function convertField(el) {
    const val = el.value || '';
    if (!val.trim()) {
      showToast('⚠️ اكتب شيئاً أولاً في المربع', false);
      return false;
    }

    let start = null;
    let end = null;
    try {
      start = el.selectionStart;
      end = el.selectionEnd;
    } catch (e) { /* ignore */ }

    const hasSelection = start !== null && end !== null && start !== end;
    const from = hasSelection ? start : 0;
    const to = hasSelection ? end : val.length;
    const original = val.substring(from, to);
    const converted = KeyConverter.convert(original);

    if (converted === original) {
      showToast('ℹ️ لا يوجد ما يحتاج للتحويل', false);
      return false;
    }

    el.focus();
    let replaced = false;
    try {
      el.setSelectionRange(from, to);
      document.execCommand('insertText', false, converted);
      replaced = (el.value === (val.slice(0, from) + converted + val.slice(to)));
    } catch (e) { /* ignore */ }

    if (!replaced) {
      if (typeof el.setRangeText === 'function') {
        el.setRangeText(converted, from, to, 'end');
      } else {
        el.value = val.slice(0, from) + converted + val.slice(to);
        const newPos = from + converted.length;
        el.selectionStart = newPos;
        el.selectionEnd = newPos;
      }
      fireInputEvents(el, converted);
    }

    showToast('✨ تم تحويل النص فوراً!');
    repositionFieldBadge(el);
    return true;
  }

  function convertEditable(hostEl) {
    hostEl.focus();
    const sel = window.getSelection();

    const hasSelectionInside =
      sel && sel.rangeCount > 0 && !sel.isCollapsed &&
      hostEl.contains(sel.anchorNode) && hostEl.contains(sel.focusNode);

    if (!hasSelectionInside && sel) {
      const range = document.createRange();
      range.selectNodeContents(hostEl);
      sel.removeAllRanges();
      sel.addRange(range);
    }

    const original = sel ? sel.toString() : '';
    if (!original.trim()) {
      showToast('⚠️ اكتب شيئاً أولاً في المربع', false);
      return false;
    }

    const converted = KeyConverter.convert(original);
    if (converted === original) {
      showToast('ℹ️ لا يوجد ما يحتاج للتحويل', false);
      return false;
    }

    let ok = false;
    try {
      ok = document.execCommand('insertText', false, converted);
    } catch (e) { /* ignore */ }

    if (!ok) {
      hostEl.textContent = converted;
      fireInputEvents(hostEl, converted);
    }

    showToast('✨ تم تحويل النص فوراً!');
    repositionFieldBadge(hostEl);
    return true;
  }

  function executeConvert(allowFallback) {
    let target = getEditable(document.activeElement);
    if (!target && allowFallback && currentTargetEl && document.contains(currentTargetEl)) {
      target = getEditable(currentTargetEl);
    }

    if (target) {
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') {
        return convertField(target);
      }
      return convertEditable(target);
    }

    // Page text highlighted
    const sel = window.getSelection();
    if (sel && sel.toString().trim()) {
      const converted = KeyConverter.convert(sel.toString());
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(converted)
          .then(() => showToast('📋 تم نسخ النتيجة المحولة للحافظة'))
          .catch(() => showToast('✨ النتيجة: ' + converted));
      } else {
        showToast('✨ النتيجة: ' + converted);
      }
      return true;
    }

    showToast('⚠️ انقر داخل أي مربع كتابة أولاً', false);
    return false;
  }

  // ---------------------------------------------------------------------------
  // Keyboard Shortcuts: Ctrl+Shift+X or Alt+X
  // ---------------------------------------------------------------------------
  document.addEventListener('keydown', (e) => {
    if (e.repeat || e.isComposing || e.code !== 'KeyX') return;
    const combo1 = (e.ctrlKey || e.metaKey) && e.shiftKey && !e.altKey;
    const combo2 = e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey;
    if (!combo1 && !combo2) return;

    e.preventDefault();
    e.stopPropagation();
    executeConvert(false);
  }, true);

  // Background Messages
  try {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      if (!request) return;
      if (request.action === 'convert_selection') {
        executeConvert(false);
        sendResponse({ status: 'ok' });
      }
    });
  } catch (e) { /* ignore */ }
})();
