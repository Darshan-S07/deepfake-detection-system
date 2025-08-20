// src/components/LiveStream.js
import React, { useRef, useState } from "react";

export default function LiveStream(){
  const localVideoRef = useRef();
  const wsRef = useRef();
  const mediaRecorderRef = useRef();

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true, video: true});
    localVideoRef.current.srcObject = stream;
    localVideoRef.current.play();

    // Open websocket
    wsRef.current = new WebSocket("ws://localhost:8000/ws/stream");
    wsRef.current.onopen = () => console.log("WS open");
    wsRef.current.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      console.log("Inference result:", msg);
      // Update UI with msg.deepfake_prob etc.
    };

    // Capture audio/video chunks via MediaRecorder
    const options = { mimeType: "audio/webm" }; // or "video/webm;codecs=vp8,opus"
    const mediaRecorder = new MediaRecorder(stream, options);
    mediaRecorderRef.current = mediaRecorder;

    mediaRecorder.ondataavailable = async (e) => {
      if (e.data && e.data.size > 0 && wsRef.current.readyState === 1) {
        const arrBuf = await e.data.arrayBuffer();
        const b64 = btoa(String.fromCharCode(...new Uint8Array(arrBuf)));
        const payload = { type: "audio", b64: b64, timestamp: Date.now() };
        wsRef.current.send(JSON.stringify(payload));
      }
    };

    // small timeslice for low latency
    mediaRecorder.start(2000); // collect every 2 seconds
  };

  const stop = () => {
    mediaRecorderRef.current && mediaRecorderRef.current.stop();
    wsRef.current && wsRef.current.close();
  };

  return (
    <div>
      <video ref={localVideoRef} autoPlay muted style={{width:300}}/>
      <div>
        <button onClick={start}>Start Stream</button>
        <button onClick={stop}>Stop</button>
      </div>
    </div>
  );
}
