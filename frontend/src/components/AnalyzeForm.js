import React, { useState } from 'react';
import { analyzeCall } from '../services/api';

const AnalyzeForm = () => {
  const [callerId, setCallerId] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [videoUrl, setVideoUrl] = useState('');
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      caller_id: callerId,
      audio_url: audioUrl,
      video_url: videoUrl,
      metadata: {}
    };

    try {
      const res = await analyzeCall(payload);
      setResult(res);
    } catch (err) {
      alert('Error analyzing call');
    }
  };

  return (
    <div>
      <h2>Analyze Call</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" placeholder="Caller ID" value={callerId} onChange={(e) => setCallerId(e.target.value)} required />
        <input type="text" placeholder="Audio URL" value={audioUrl} onChange={(e) => setAudioUrl(e.target.value)} required />
        <input type="text" placeholder="Video URL" value={videoUrl} onChange={(e) => setVideoUrl(e.target.value)} required />
        <button type="submit">Analyze</button>
      </form>

      {result && (
        <div style={{ marginTop: '20px' }}>
          <h3>Result:</h3>
          <p><strong>Caller ID:</strong> {result.caller_id}</p>
          <p><strong>Deepfake Detected:</strong> {result.deepfake_detected ? 'Yes' : 'No'}</p>
          <p><strong>Spam Detected:</strong> {result.spam_detected ? 'Yes' : 'No'}</p>
          <p><strong>Recommendation:</strong> {result.recommendation}</p>
        </div>
      )}
    </div>
  );
};

export default AnalyzeForm;
