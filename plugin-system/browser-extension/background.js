let capturedStream = null;

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "REQUEST_AUDIO_STREAM") {
  
      chrome.tabCapture.capture(
        { audio: true, video: false },
        (stream) => {
          if (!stream) {
            sendResponse({ success: false });
            return;
          }
  
          // Store stream globally
          chrome.storage.session.set({ audioStreamId: "active" });
  
          sendResponse({ success: true });
        }
      );
  
      return true; // KEEP ASYNC CHANNEL OPEN
    }
  });
  
// background.js - minimal service worker to keep extension alive and allow future messaging
chrome.runtime.onInstalled.addListener(() => {
  console.log("Deepfake Detector installed.");
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // placeholder for future features (popup -> background)
  if (msg === 'PING') sendResponse('PONG');
});

// background.js (add this listener)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "SAVE_SESSION") {
    const session = msg.session || {};
    const key = `session_${Date.now()}`;
    chrome.storage.local.set({ [key]: session }, () => {
      console.log("Session saved:", key);
      sendResponse({ saved: true, key });
    });
    return true; // indicate async
  }
});


async function saveDetectionLog(result) {
  const stored = await chrome.storage.local.get(["token"]);
  if (!stored.token) {
      console.warn("User not logged in — skipping log save.");
      return;
  }

  await fetch("http://localhost:8000/call/save", {
      method: "POST",
      headers: {
          "Authorization": `Bearer ${stored.token}`,
          "Content-Type": "application/json"
      },
      body: JSON.stringify(result)
  });
}

// Expose listener so content script can send logs
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === "save_log") {
      saveDetectionLog(msg.data);
      sendResponse({ status: "ok" });
  }
});
