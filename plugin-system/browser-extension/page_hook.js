// page_hook.js - injected into page context (runs with page privileges)
(() => {
  if (window.__DF_PAGE_HOOK__) return;
  window.__DF_PAGE_HOOK__ = true;
  window.__DF_STREAMS__ = window.__DF_STREAMS__ || {};

  const OrigPC = window.RTCPeerConnection;
  if (!OrigPC) return;

  function PatchedPC(...args) {
    const pc = new OrigPC(...args);

    pc.addEventListener('track', (ev) => {
      try {
        // store streams and notify content script via postMessage
        const streams = ev.streams || [];
        streams.forEach(s => {
          if (!s || !s.id) return;
          window.__DF_STREAMS__[s.id] = s;
          window.postMessage({ type: 'DF_STREAM', streamId: s.id }, '*');
        });
      } catch (e) {
        // ignore
      }
    });

    return pc;
  }
  PatchedPC.prototype = OrigPC.prototype;
  window.RTCPeerConnection = PatchedPC;
})();
