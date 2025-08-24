// // src/components/LiveStream.js
// import React, { useRef, useState } from "react";

// export default function LiveStream(){
//   const localVideoRef = useRef();
//   const wsRef = useRef();
//   const mediaRecorderRef = useRef();

//   const start = async () => {
//     const stream = await navigator.mediaDevices.getUserMedia({audio: true, video: true});
//     localVideoRef.current.srcObject = stream;
//     localVideoRef.current.play();

//     // Open websocket
//     wsRef.current = new WebSocket("ws://localhost:8000/ws/stream");
//     wsRef.current.onopen = () => console.log("WS open");
//     wsRef.current.onmessage = (evt) => {
//       const msg = JSON.parse(evt.data);
//       console.log("Inference result:", msg);
//       // Update UI with msg.deepfake_prob etc.
//     };

//     // Capture audio/video chunks via MediaRecorder
//     const options = { mimeType: "audio/webm" }; // or "video/webm;codecs=vp8,opus"
//     const mediaRecorder = new MediaRecorder(stream, options);
//     mediaRecorderRef.current = mediaRecorder;

//     mediaRecorder.ondataavailable = async (e) => {
//       if (e.data && e.data.size > 0 && wsRef.current.readyState === 1) {
//         const arrBuf = await e.data.arrayBuffer();
//         const b64 = btoa(String.fromCharCode(...new Uint8Array(arrBuf)));
//         const payload = { type: "audio", b64: b64, timestamp: Date.now() };
//         wsRef.current.send(JSON.stringify(payload));
//       }
//     };

//     // small timeslice for low latency
//     mediaRecorder.start(2000); // collect every 2 seconds
//   };

//   const stop = () => {
//     mediaRecorderRef.current && mediaRecorderRef.current.stop();
//     wsRef.current && wsRef.current.close();
//   };

//   return (
//     <div>
//       <video ref={localVideoRef} autoPlay muted style={{width:300}}/>
//       <div>
//         <button onClick={start}>Start Stream</button>
//         <button onClick={stop}>Stop</button>
//       </div>
//     </div>
//   );
// }
import React, { useRef, useState } from "react";

export default function LiveStream(){
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const recRef = useRef(null);
  const [status, setStatus] = useState("idle");

  const start = async () => {
    const token = localStorage.getItem("token");
    if(!token){ alert("Login first"); return; }

    const stream = await navigator.mediaDevices.getUserMedia({audio:true, video:true});
    videoRef.current.srcObject = stream; videoRef.current.play();

    const ws = new WebSocket("ws://localhost:8000/ws/stream");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({auth: `Bearer ${token}`}));
      setStatus("connected");
    };
    ws.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if(msg.deepfake_prob !== undefined){
        console.log("Result:", msg);
      }
    };
    ws.onclose = () => setStatus("closed");

    const rec = new MediaRecorder(stream, {mimeType: "audio/webm"});
    recRef.current = rec;
    rec.ondataavailable = async (e) => {
      if (e.data && e.data.size > 0 && ws.readyState === 1){
        const arr = new Uint8Array(await e.data.arrayBuffer());
        // convert to base64 quickly
        let bin = ""; for (let i=0;i<arr.length;i++) bin += String.fromCharCode(arr[i]);
        const b64 = btoa(bin);
        ws.send(JSON.stringify({type:"audio", b64, timestamp: Date.now()}));
      }
    };
    rec.start(1500); // 1.5s chunks
  };

  const stop = () => {
    recRef.current && recRef.current.stop();
    wsRef.current && wsRef.current.close();
    setStatus("stopped");
  };

  return (
    <div>
      <h3>Live Stream (Demo)</h3>
      <video ref={videoRef} autoPlay muted style={{width: 320}}/>
      <div style={{marginTop: 8}}>
        <button onClick={start}>Start</button>
        <button onClick={stop}>Stop</button>
        <span style={{marginLeft: 10}}>Status: {status}</span>
      </div>
    </div>
  );
}
