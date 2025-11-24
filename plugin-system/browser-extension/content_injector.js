/* content_injector.js - Enhanced: live score, mute pause, lip-sync, TTS heuristic, session reports */

(() => {
  if (window.__DF_RUNNING__) return;
  window.__DF_RUNNING__ = true;
  console.log("%c[Deepfake Detector Loaded - enhanced]", "color:#00e676;font-weight:bold");

  const allowedHosts = ["meet.google.com","zoom.us","teams.microsoft.com"];
  if (!allowedHosts.some(h => location.hostname.includes(h))) return;

  // Config
  const WS_URL = "ws://127.0.0.1:8000:8000/ws";
  const VIDEO_INTERVAL = 1500;      // ms between frames
  const AUDIO_SAMPLE_WINDOW = 0.5;  // seconds per PCM chunk (audioWorklet)
  const LIPSYNC_LAG_THRESHOLD_MS = 300; // if avg lag > this => suspicious
  const TTS_SPECTRAL_FLATNESS_THRESHOLD = 0.55; // heuristic value
  const TTS_ZCR_THRESHOLD = 0.05; // zero-crossing rate threshold heuristic

  // State
  let ws = null;
  let processedStreams = new WeakSet();
  let audioContexts = new WeakMap();
  let sessionLog = { start: Date.now(), events: [], audioChunksSent: 0, videoFramesSent: 0, scores: [] };

  // UI: overlay + chart canvas
  function createUI() {
    if (document.getElementById("__df_box")) return;
    const box = document.createElement("div");
    box.id = "__df_box";
    Object.assign(box.style, {
      position:"fixed", right:"18px", top:"18px", zIndex:2147483647,
      background:"rgba(0,0,0,0.85)", color:"#fff", padding:"10px", borderRadius:"10px",
      fontFamily:"system-ui", width:"260px", boxShadow:"0 6px 18px rgba(0,0,0,0.4)"
    });

    box.innerHTML = `
      <div style="font-weight:600;margin-bottom:8px">Deepfake Monitor</div>
      <div id="__df_status" style="font-size:13px;margin-bottom:8px">Waiting for meeting…</div>
      <canvas id="__df_chart" width="240" height="60" style="background:rgba(255,255,255,0.03);border-radius:6px"></canvas>
      <div style="display:flex;gap:6px;margin-top:8px">
        <button id="__df_download" style="flex:1;padding:6px;border-radius:6px;border:none;cursor:pointer">Download report</button>
        <button id="__df_reset" style="padding:6px;border-radius:6px;border:none;cursor:pointer">Reset</button>
      </div>
    `;
    document.body.appendChild(box);

    document.getElementById("__df_download").addEventListener("click", () => {
      chrome.runtime?.sendMessage?.({ type: "SAVE_SESSION", session: sessionLog });
      // attempt PDF via jsPDF if available, else download JSON
      if (window.jsPDF) {
        const doc = new jsPDF();
        doc.setFontSize(12);
        doc.text("Deepfake Detection Session Report", 10, 12);
        doc.text(`Start: ${new Date(sessionLog.start).toLocaleString()}`, 10, 20);
        doc.text(`Events: ${sessionLog.events.length}`, 10, 28);
        doc.text(`Audio chunks sent: ${sessionLog.audioChunksSent}`, 10, 36);
        doc.text(`Video frames sent: ${sessionLog.videoFramesSent}`, 10, 44);
        doc.text(`Avg score: ${avg(sessionLog.scores).toFixed(3)}`, 10, 52);
        doc.save("deepfake-session.pdf");
      } else {
        const blob = new Blob([JSON.stringify(sessionLog, null, 2)], {type:"application/json"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "deepfake-session.json"; a.click();
        URL.revokeObjectURL(url);
      }
    });

    document.getElementById("__df_reset").addEventListener("click", () => {
      sessionLog = { start: Date.now(), events: [], audioChunksSent:0, videoFramesSent:0, scores:[] };
      clearChart();
      updateUI("Session reset", "#fff");
    });
  }

  function updateUI(text, color="#fff") {
    const el = document.getElementById("__df_status"); if (!el) return;
    el.textContent = text; el.style.color = color;
  }

  // small chart (simple moving sparkline of confidence)
  const chart = { ctx:null, data:[] };
  function initChart() {
    const c = document.getElementById("__df_chart");
    if (!c) return;
    chart.ctx = c.getContext("2d");
    chart.data = [];
    drawChart();
  }
  function pushScore(v) {
    chart.data.push(v);
    if (chart.data.length > 60) chart.data.shift();
    drawChart();
  }
  function clearChart() { chart.data = []; drawChart(); }
  function drawChart() {
    if (!chart.ctx) return;
    const ctx = chart.ctx; const w = ctx.canvas.width, h = ctx.canvas.height;
    ctx.clearRect(0,0,w,h);
    // background
    ctx.fillStyle = "rgba(255,255,255,0.02)"; ctx.fillRect(0,0,w,h);
    // axis baseline
    ctx.strokeStyle = "rgba(255,255,255,0.06)"; ctx.beginPath(); ctx.moveTo(0,h-12); ctx.lineTo(w,h-12); ctx.stroke();
    // sparkline
    if (chart.data.length === 0) return;
    const max = 1; const min = 0;
    ctx.beginPath();
    for (let i=0;i<chart.data.length;i++){
      const x = (i/(chart.data.length-1||1))*w;
      const y = h-12 - ((chart.data[i]-min)/(max-min))*(h-20);
      if (i===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }
    // gradient
    const g = ctx.createLinearGradient(0,0,0,h);
    g.addColorStop(0,"rgba(255,0,0,0.9)"); g.addColorStop(1,"rgba(0,200,100,0.9)");
    ctx.strokeStyle = g; ctx.lineWidth = 2; ctx.stroke();
  }

  // helpers
  function avg(arr) { if(!arr||arr.length===0) return 0; return arr.reduce((a,b)=>a+b,0)/arr.length; }

  // base64 helper (chunk-safe)
  function base64FromArrayBuffer(arrayBuffer) {
    const chunk = 0x8000; const u8 = new Uint8Array(arrayBuffer); let s = "";
    for (let i=0;i<u8.length;i+=chunk) s += String.fromCharCode.apply(null,u8.subarray(i,i+chunk));
    return btoa(s);
  }

  // websocket
  function connectWS() {
    if (ws && (ws.readyState===0 || ws.readyState===1)) return;
    try {
      ws = new WebSocket(WS_URL);
    } catch(e) { console.error("WS create err",e); updateUI("Backend offline", "#ff9800"); setTimeout(connectWS,2000); return; }

    ws.onopen = () => { console.log("WS open"); updateUI("Connected to backend ✓","#4caf50"); };
    ws.onmessage = (evt) => {
      // expect backend: { risk: "LOW"|"MEDIUM"|"HIGH", score: 0.0..1.0 } or numeric "score"
      let msg = null;
      try { msg = JSON.parse(evt.data); } catch(e){ return; }
      let score = null;
      if (typeof msg.score === "number") score = msg.score;
      else if (msg.risk) {
        if (msg.risk === "LOW") score = 0.15;
        if (msg.risk === "MEDIUM") score = 0.55;
        if (msg.risk === "HIGH") score = 0.9;
      }
      if (score === null) return;
      sessionLog.scores.push(score); pushScore(score);
      // show crisp UI per thresholds
      if (score >= 0.8) updateUI("🚨 HIGH — Deepfake detected", "#ff1744");
      else if (score >= 0.5) updateUI("⚠ Suspicious media", "#ffb300");
      else updateUI("🟢 Low risk", "#4caf50");

      // save event
      sessionLog.events.push({ t:Date.now(), type:'SCORE', score });
    };
    ws.onclose = () => { console.warn("ws closed"); updateUI("Backend disconnected — retrying","#ff5722"); setTimeout(connectWS,2000); };
    ws.onerror = (e) => { console.error("ws err",e); try{ws.close()}catch{}; };
  }

  // Lip sync: basic cross-correlation between audio energy peaks & frame motion energy
  // We'll maintain short rolling arrays of timestamps and energies
  function analyzeLipSync(audioEnergyTimes, frameMotionTimes) {
    if (audioEnergyTimes.length < 4 || frameMotionTimes.length < 4) return { suspicious:false, lagMs:0, corr:0 };
    // compute average lag (frame_time - audio_time) at nearest neighbor
    const lags = [];
    for (let ft of frameMotionTimes) {
      // find closest audio
      let closest = null; let bestd = Infinity;
      for (let at of audioEnergyTimes) {
        const d = Math.abs(ft.t - at.t);
        if (d < bestd) { bestd = d; closest = at; }
      }
      if (closest) lags.push(ft.t - closest.t);
    }
    if (lags.length===0) return { suspicious:false, lagMs:0, corr:0 };
    const meanLag = lags.reduce((a,b)=>a+b,0)/lags.length;
    const lagMs = meanLag;
    const suspicious = Math.abs(lagMs) > LIPSYNC_LAG_THRESHOLD_MS;
    return { suspicious, lagMs, corr:0 };
  }

  // Simple TTS detection heuristics on PCM chunk:
  // - ZCR (zero crossing rate) low => synthetic
  // - spectral flatness high => synthetic (flat spectrum)
  function computeZCR(float32Array) {
    let z=0;
    for (let i=1;i<float32Array.length;i++){
      if ((float32Array[i-1] < 0 && float32Array[i] >= 0) || (float32Array[i-1] >= 0 && float32Array[i] < 0)) z++;
    }
    return z/float32Array.length;
  }

  // spectral flatness approximate via small FFT using builtin AnalyserNode (fast path)
  // we will create an AnalyserNode per audio stream and poll it periodically
  function computeSpectralFlatnessFromAnalyser(analyser) {
    const N = analyser.frequencyBinCount;
    const arr = new Float32Array(N);
    analyser.getFloatFrequencyData(arr); // dB values
    // convert to magnitude (not perfect but ok)
    const mags = arr.map(v => Math.pow(10, v/20));
    let geo = 1; let arith = 0; let cnt = 0;
    for (let m of mags) { if (m<=0) continue; geo *= Math.pow(m, 1/N); arith += m; cnt++; }
    if (cnt===0) return 0;
    arith = arith/cnt;
    const flatness = geo / (arith || 1e-12);
    return flatness;
  }

  // start processing when remote stream available
  async function startStreamsForRemote(stream) {
    if (!stream || processedStreams.has(stream)) return;
    processedStreams.add(stream);
    connectWS();
    updateUI("Meeting detected — preparing analysis…","#00b4d8");
    sessionLog.events.push({ t:Date.now(), type:'STREAM_START' });

    // Rolling arrays for lip-sync
    const audioEnergyTimes = []; // {t:ms, e:energy}
    const frameMotionTimes = []; // {t:ms, m:motion}

    // AUDIO
    if (stream.getAudioTracks().length) {
      try {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate:16000 });
        audioContexts.set(stream, audioCtx);

        // create analyser for spectral flatness
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;

        await audioCtx.audioWorklet.addModule(chrome.runtime.getURL("audioWorkletProcessor.js"));
        const src = audioCtx.createMediaStreamSource(stream);
        const node = new AudioWorkletNode(audioCtx, "deepfake-audio-processor");

        // connect analyser in chain: src -> analyser -> node (node expects input)
        try {
          // Some browsers allow chaining: src -> node -> analyser -> destination (but analyser reads after node)
          src.connect(analyser);
          analyser.connect(node);
        } catch(e) {
          // fallback: src -> node and create a secondary analyser via MediaStream
          try {
            src.connect(node);
            // create duplicate stream for analyser by using src.mediaStream (not standard) - fallback: skip analyser
          } catch(e2) { src.connect(node); }
        }

        node.port.onmessage = (evt) => {
          const payload = evt.data;
          if (!payload || payload.type !== "AUDIO_CHUNK" || !payload.pcm) return;
          // payload.pcm is Float32Array
          const pcm = payload.pcm;
          const now = Date.now();
          // compute RMS energy
          let sum=0; for (let i=0;i<pcm.length;i++){ sum += pcm[i]*pcm[i]; }
          const rms = Math.sqrt(sum/pcm.length);
          audioEnergyTimes.push({ t: now, e: rms });
          if (audioEnergyTimes.length>30) audioEnergyTimes.shift();

          // TTS heuristics
          const zcr = computeZCR(pcm);
          let spectralFlatness = 0;
          try { spectralFlatness = computeSpectralFlatnessFromAnalyser(analyser); } catch(e){ /*ignore*/ }

          // compute TTS score: normalized combination
          const ttsScore = ( (spectralFlatness||0) + (1 - Math.min(1, zcr/ TTS_ZCR_THRESHOLD)) ) / 2;
          // record event
          sessionLog.events.push({ t: now, type:'AUDIO_FEATURE', rms, zcr, spectralFlatness, ttsScore });
          // if ttsScore high => mark suspicious
          if (ttsScore >= TTS_SPECTRAL_FLATNESS_THRESHOLD) {
            sessionLog.events.push({ t: now, type:'TTS_SUSPECT', score: ttsScore });
            // notify UI (but don't spam)
            updateUI("⚠ Possible synthetic voice detected", "#ffb300");
          }

          // send audio PCM base64 to backend for ML inference
          try {
            const ab = pcm.buffer;
            const base64 = base64FromArrayBuffer(ab);
            if (ws && ws.readyState===1) {
              ws.send(JSON.stringify({ type:'AUDIO_FRAME', data: base64 }));
              sessionLog.audioChunksSent++;
              // log that we've sent
            }
          } catch(e){ console.error("failed send audio",e); }
        };

        // silent connect
        const gain = audioCtx.createGain(); gain.gain.value = 0;
        src.connect(node).connect(gain).connect(audioCtx.destination);

        updateUI("Analyzing audio…","#00b4d8");
        sessionLog.events.push({ t:Date.now(), type:'AUDIO_STARTED' });
      } catch(e) {
        console.error("audio init failed", e);
        updateUI("Audio engine failed","#ff1744");
      }
    }

    // VIDEO capture + compute motion per frame (frame difference)
    if (stream.getVideoTracks().length) {
      try {
        const video = document.createElement("video");
        video.srcObject = stream; video.muted = true; video.playsInline = true; video.style.display="none";
        document.documentElement.appendChild(video);

        const canvasA = document.createElement("canvas");
        const ctxA = canvasA.getContext("2d");
        let prevImg = null;

        // ensure video plays
        try { await video.play(); } catch(e) { console.warn("video play failed",e); }

        const sendFrameLoop = async () => {
          if (!ws || ws.readyState !== 1) { setTimeout(sendFrameLoop, 800); return; }
          if (video.readyState < 2) { setTimeout(sendFrameLoop, 400); return; }
          // size
          const w = Math.max(160, Math.min(640, video.videoWidth||320));
          const h = Math.max(90, Math.min(360, video.videoHeight||180));
          canvasA.width = w; canvasA.height = h;
          try {
            ctxA.drawImage(video,0,0,w,h);
            const imgData = ctxA.getImageData(0,0,w,h);
            // compute simple motion metric: sum absolute diff from prev grayscale
            let motion = 0;
            const gray = new Uint8Array(w*h);
            for (let i=0, j=0;i<imgData.data.length;i+=4, j++){
              gray[j] = (imgData.data[i]*0.3 + imgData.data[i+1]*0.59 + imgData.data[i+2]*0.11) | 0;
            }
            if (prevImg) {
              let s=0;
              for (let k=0;k<gray.length;k++){
                s += Math.abs(gray[k] - prevImg[k]);
              }
              motion = s/gray.length;
            }
            prevImg = gray;
            const now = Date.now();
            frameMotionTimes.push({ t: now, m: motion });
            if (frameMotionTimes.length>30) frameMotionTimes.shift();

            // crop for mouth region heuristic (we approximate bottom center region)
            // not using face detection (heavy), this is a heuristic
            // send frame to backend
            const blob = await new Promise(r=>canvasA.toBlob(r,'image/jpeg',0.6));
            const ab = await blob.arrayBuffer();
            const base64 = base64FromArrayBuffer(ab);
            if (ws && ws.readyState===1) {
              ws.send(JSON.stringify({ type:'VIDEO_FRAME', data: base64 }));
              sessionLog.videoFramesSent++;
            }

            // analyze lip-sync on short window
            const lip = analyzeLipSync(audioEnergyTimes, frameMotionTimes);
            if (lip.suspicious) {
              sessionLog.events.push({ t:now, type:'LIPSYNC_SUSPECT', lagMs:lip.lagMs });
              updateUI("⚠ Lip-sync mismatch detected", "#ffb300");
            }
          } catch(err){ console.error("video loop err",err); }
          setTimeout(sendFrameLoop, VIDEO_INTERVAL);
        };

        video.addEventListener("playing", () => { console.log("video playing -> start frames"); sendFrameLoop(); });

        if (video.readyState >=2 && !video.paused) sendFrameLoop();
        sessionLog.events.push({ t:Date.now(), type:'VIDEO_STARTED' });
      } catch(e){ console.error("video init failed", e); updateUI("Video engine failed","#ff1744"); }
    }

    // MUTE / ENABLE monitoring - pause when tracks disabled
    (function watchEnableDisable() {
      const tracks = stream.getTracks();
      tracks.forEach(t => {
        t.addEventListener('ended', ()=> sessionLog.events.push({ t:Date.now(), type:'TRACK_ENDED', kind:t.kind }));
        t.addEventListener('mute', ()=> { sessionLog.events.push({ t:Date.now(), type:'TRACK_MUTED', kind:t.kind}); updateUI("Remote muted — analysis paused","#bdbdbd"); });
        t.addEventListener('unmute', ()=> { sessionLog.events.push({ t:Date.now(), type:'TRACK_UNMUTED', kind:t.kind}); updateUI("Remote unmuted — resuming","#00b4d8"); });
      });
    })();

    updateUI("Analyzing call (audio+video)…", "#00b4d8");
  }

  // fallback: watch normal video elements if page_hook doesn't post
  function fallbackWatcher() {
    const run = () => {
      const vids = [...document.querySelectorAll("video")];
      vids.forEach(v => { if (v && v.srcObject) startStreamsForRemote(v.srcObject); });
    };
    run();
    new MutationObserver(run).observe(document.documentElement || document.body, { childList:true, subtree:true });
  }

  // INIT
  setTimeout(() => {
    createUI(); initChart(); connectWS();
    // inject page_hook so page can post DF_STREAM messages (if you use page_hook.js)
    const s = document.createElement('script');
    s.src = chrome.runtime.getURL('page_hook.js');
    (document.head||document.documentElement).appendChild(s);
    s.onload = ()=>s.remove();
    fallbackWatcher();
    updateUI("Waiting for meeting…","white");
  }, 800);

  // Expose sessionLog for debugging
  window.__DF_SESSION = sessionLog;
})();
