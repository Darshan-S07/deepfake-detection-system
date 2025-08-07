import React, { useRef } from 'react';

function Call() {
  const localVideo = useRef();
  const remoteVideo = useRef();

  const startCall = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.current.srcObject = stream;
    localVideo.current.play();

    // Simulate peer connection
    remoteVideo.current.srcObject = stream;
    remoteVideo.current.play();
  };

  return (
    <div className="call-section">
      <button onClick={startCall}>Start Call</button>
      <div className="video-container">
        <video ref={localVideo} className="video" />
        <video ref={remoteVideo} className="video" />
      </div>
    </div>
  );
}

export default Call;
