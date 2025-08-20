
// }

// export default App;
import React, { useState } from "react";
import Signup from "./components/Signup";
import Login from "./components/Login";
import FileUpload from "./components/FileUpload";
import LiveStream from "./components/LiveStream";

function App(){
  const [loggedIn, setLoggedIn] = useState(!!localStorage.getItem("token"));

  return (
    <div style={{padding:"1.5rem", fontFamily:"sans-serif"}}>
      <h2>SecureCallX — Hybrid Call Security (Demo)</h2>
      {!loggedIn && (
        <>
          <Signup />
          <Login onLogin={() => setLoggedIn(true)} />
        </>
      )}
      {loggedIn && (
        <>
          <FileUpload />
          <hr />
          <LiveStream />
          <div style={{marginTop:10}}>
            <button onClick={()=>{ localStorage.removeItem("token"); window.location.reload(); }}>
              Logout
            </button>
          </div>
        </>
      )}
    </div>
  );
}
export default App;
