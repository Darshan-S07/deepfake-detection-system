import React, { useState } from "react";
import { login } from "../services/api";

export default function Login({ onLogin }){
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [msg, setMsg] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      const res = await login(u, p);
      localStorage.setItem("token", res.data.access_token);
      setMsg("Logged in");
      onLogin && onLogin(true);
    } catch (err) {
      setMsg("Login failed");
    }
  };

  return (
    <div>
      <h3>Login</h3>
      <form onSubmit={submit}>
        <input placeholder="username" value={u} onChange={e=>setU(e.target.value)} />
        <input type="password" placeholder="password" value={p} onChange={e=>setP(e.target.value)} />
        <button>Login</button>
      </form>
      {msg && <p>{msg}</p>}
    </div>
  );
}
