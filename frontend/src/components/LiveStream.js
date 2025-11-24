// src/components/LiveStream.js
import React, { useRef, useState } from "react";

export default function LiveStream() {
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const recRef = useRef(null);
  const [status, setStatus] = useState("idle");

  const start = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Login first");
      return;
    }

    let stream;
    try {
      // Request audio+video
      stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: true,
      });
      console.log("Got user media:", stream);
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    } catch (err) {
      console.error("getUserMedia failed:", err);
      alert("Could not access microphone/camera. Check permissions.");
      return;
    }

    // Check if MediaRecorder exists
    if (typeof MediaRecorder === "undefined") {
      alert("MediaRecorder not supported in this browser.");
      setStatus("unsupported");
      return;
    }

    // Open WebSocket
    const ws = new WebSocket("ws://localhost:8000/ws/stream");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ auth: `Bearer ${token}` }));
      setStatus("connected");
    };
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.deepfake_prob !== undefined) {
        console.log("Result:", msg);
      }
    };
    ws.onclose = () => setStatus("closed");

    // ✅ Safe MediaRecorder creation with fallbacks
    let rec;
    try {
      rec = new MediaRecorder(stream, { mimeType: "audio/webm;codecs=opus" });
      rec.start(1500);
      console.log("Recording started with:", rec.mimeType);
    } catch (err1) {
      console.warn("audio/webm;codecs=opus failed, trying audio/webm", err1);
      try {
        rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
        rec.start(1500);
        console.log("Recording started with:", rec.mimeType);
      } catch (err2) {
        console.warn("audio/webm failed, trying browser default", err2);
        try {
          rec = new MediaRecorder(stream); // let browser decide
          rec.start(1500);
          console.log("Recording started with browser default:", rec.mimeType);
        } catch (err3) {
          console.error("MediaRecorder could not start at all", err3);
          alert("Recording not supported in this browser.");
          return;
        }
      }
    }
    recRef.current = rec;

    // Handle chunks
    rec.ondataavailable = async (e) => {
      if (e.data && e.data.size > 0 && ws.readyState === 1) {
        const arr = new Uint8Array(await e.data.arrayBuffer());
        let bin = "";
        for (let i = 0; i < arr.length; i++) bin += String.fromCharCode(arr[i]);
        const b64 = btoa(bin);
        ws.send(JSON.stringify({ type: "audio", b64, timestamp: Date.now() }));
      }
    };

    setStatus("recording");
  };

  const stop = () => {
    recRef.current && recRef.current.stop();
    wsRef.current && wsRef.current.close();
    setStatus("stopped");
  };

  return (
    <div>
      <h3>Live Stream (Demo)</h3>
      <video ref={videoRef} autoPlay muted style={{ width: 320 }} />
      <div style={{ marginTop: 8 }}>
        <button onClick={start}>Start</button>
        <button onClick={stop}>Stop</button>
        <span style={{ marginLeft: 10 }}>Status: {status}</span>
      </div>
    </div>
  );
}
