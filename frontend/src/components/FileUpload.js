// src/components/FileUpload.js
import React, { useState } from "react";
import axios from "axios";

export default function FileUpload(){
  const [callerId, setCallerId] = useState("");
  const [audioFile, setAudioFile] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [result, setResult] = useState(null);

  const submit = async (e) => {
    e.preventDefault();
    const form = new FormData();
    form.append("caller_id", callerId);
    if(audioFile) form.append("audio", audioFile);
    if(videoFile) form.append("video", videoFile);

    try {
      const res = await axios.post("http://localhost:8000/upload-media", form, {
        headers: {"Content-Type": "multipart/form-data"}
      });
      setResult(res.data);
    } catch (err) {
      alert("Upload failed");
      console.error(err);
    }
  };

  return (
    <form onSubmit={submit}>
      <input value={callerId} onChange={e=>setCallerId(e.target.value)} placeholder="Caller ID" required />
      <div>
        <label>Audio</label>
        <input type="file" accept="audio/*" onChange={e=>setAudioFile(e.target.files[0])}/>
      </div>
      <div>
        <label>Video</label>
        <input type="file" accept="video/*" onChange={e=>setVideoFile(e.target.files[0])}/>
      </div>
      <button type="submit">Upload & Analyze</button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </form>
  );
}
