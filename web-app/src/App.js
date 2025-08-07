import React from 'react';
import Call from './components/Call';
import Alerts from './components/Alerts';
import './styles.css';

function App() {
  return (
    <div className="app-container">
      <h1>SecureCallX</h1>
      <Call />
      <Alerts />
    </div>
  );
}

export default App;
