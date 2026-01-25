"use client";

import { useState } from "react";
import api from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    try {
      const resp = await api.post("/auth/login", { email, senha });
      localStorage.setItem("access_token", resp.data.access_token);
      window.location.href = "/";
    } catch {
      setError("Login failed");
    }
  }

  return (
    <div className="min-h-screen grid place-items-center p-6">
      <div className="w-full max-w-md rounded-3xl bg-white/80 p-8 shadow-xl">
        <h1 className="text-3xl font-display">Bem-vindo</h1>
        <p className="text-sm text-gray-500">Acesse o painel do studio</p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <input
            className="w-full rounded-xl border border-black/10 p-3"
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="w-full rounded-xl border border-black/10 p-3"
            placeholder="senha"
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button className="w-full rounded-xl bg-black py-3 text-white">Entrar</button>
        </form>
      </div>
    </div>
  );
}
