import React, { useEffect, useState } from 'react';

const alerts = [
  "⚠️ Spam Call Detected",
  "🎭 Deepfake Audio Detected",
  "🔐 Call Accessed Your Messages",
];

function Alerts() {
  const [currentAlert, setCurrentAlert] = useState(null);

  useEffect(() => {
    const interval = setInterval(() => {
      const random = Math.floor(Math.random() * alerts.length);
      setCurrentAlert(alerts[random]);
    }, 7000); // every 7 sec

    return () => clearInterval(interval);
  }, []);

  return currentAlert ? (
    <div className="alert-box">
      {currentAlert}
    </div>
  ) : null;
}

export default Alerts;
