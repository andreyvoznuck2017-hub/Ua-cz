(() => {
  'use strict';
  if (window.top !== window || location.origin !== 'https://test.jkunis.eu') return;
  const handler = window.webkit?.messageHandlers?.svoyiHost;
  if (!handler || window.__svoyiIOSHost) return;
  Object.defineProperty(window, '__svoyiIOSHost', { value: true });
  const invoke = (type, payload = {}) => handler.postMessage({ type, ...payload });
  let queued = false, lastTheme = '';
  function syncTheme() {
    queued = false;
    if (!document.body) return;
    const body = getComputedStyle(document.body);
    const rgb = body.backgroundColor.match(/^rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:\s*[,/]\s*([\d.]+))?\s*\)$/);
    if (!rgb || (rgb[4] != null && Number(rgb[4]) < 0.5)) return;
    const color = rgb.slice(1, 4).map(Number);
    if (color.some(n => n < 0 || n > 255)) return;
    const key = color.join(',');
    if (key === lastTheme) return;
    lastTheme = key;
    invoke('theme', { rgb: color }).catch(() => {});
  }
  function scheduleTheme() {
    if (queued) return;
    queued = true;
    setTimeout(syncTheme, 100);
  }
  function start() {
    new MutationObserver(scheduleTheme).observe(document.documentElement,
      { attributes: true, attributeFilter: ['class', 'style', 'data-theme'] });
    if (document.body) new MutationObserver(scheduleTheme).observe(document.body,
      { attributes: true, attributeFilter: ['class', 'style', 'data-theme'] });
    scheduleTheme();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
  document.addEventListener('svoyi:pagechange', scheduleTheme);
  window.addEventListener('pageshow', scheduleTheme);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', scheduleTheme);

  // Preserve native Web Share when WebKit already provides it. Fallback supports text/URL only.
  if (typeof navigator.share !== 'function') {
    const share = async data => {
      if (!navigator.userActivation?.isActive) throw new DOMException('Потрібне натискання користувача.', 'NotAllowedError');
      if (!data || data.files || !['title', 'text', 'url'].some(k => typeof data[k] === 'string' && data[k]))
        throw new TypeError('Підтримується лише текст або посилання.');
      const answer = await invoke('share', {
        title: String(data.title || '').slice(0, 200),
        text: String(data.text || '').slice(0, 10000), url: String(data.url || '').slice(0, 4096)
      });
      if (!answer?.completed) throw new DOMException('Поширення скасовано.', 'AbortError');
    };
    try {
      Object.defineProperty(navigator, 'share', { configurable: true, value: share });
      Object.defineProperty(navigator, 'canShare', { configurable: true, value: data =>
        !!data && !data.files && ['title', 'text', 'url'].some(k => typeof data[k] === 'string' && data[k].length > 0) });
    } catch (_) { /* A read-only browser property must not break the page. */ }
  }
})();
