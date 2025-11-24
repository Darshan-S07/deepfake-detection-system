import React, { useState } from "react";
import { signup } from "../services/api";

export default function Signup(){
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [msg, setMsg] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      await signup(u, p);
      setMsg("User created. Please login.");
    } catch (err) {
      setMsg("Signup failed");
    }
  };

  return (
    <div>
      <h3>Signup</h3>
      <form onSubmit={submit}>
        <input placeholder="username" value={u} onChange={e=>setU(e.target.value)} />
        <input type="password" placeholder="password" value={p} onChange={e=>setP(e.target.value)} />
        <button>Signup</button>
      </form>
      {msg && <p>{msg}</p>}
    </div>
  );
}
