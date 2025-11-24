(function () {
    if (window.__DF_UI_ACTIVE__) return;
    window.__DF_UI_ACTIVE__ = true;

    const panel = document.createElement("div");
    panel.id = "deepfake-alert-panel";
    panel.style = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 14px 18px;
        background: rgba(0,0,0,0.75);
        color: white;
        border-radius: 12px;
        font-size: 16px;
        font-weight: bold;
        z-index: 100000;
        font-family: system-ui;
    `;
    panel.innerText = "🔍 Analyzing live call...";
    document.body.appendChild(panel);

    chrome.runtime.onMessage.addListener(({ type, result }) => {
        if (type === "AUDIO_RESULT" || type === "VIDEO_RESULT") {
            if (result.risk > 0.7) {
                panel.style.background = "rgba(200, 0, 0, 0.85)";
                panel.innerText = `⚠️ Deepfake Detected | Risk: ${(result.risk * 100).toFixed(1)}%`;
            } else {
                panel.style.background = "rgba(0, 128, 0, 0.85)";
                panel.innerText = `🟢 Safe | Risk: ${(result.risk * 100).toFixed(1)}%`;
            }
        }
    });
})();
