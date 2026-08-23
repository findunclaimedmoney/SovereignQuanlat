import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

const formatError = (detail) => {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).join(" ");
  return String(detail);
};

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setError("");
    setLoading(true);
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await register(name, email, password);
      }
      navigate("/dashboard");
    } catch (e) {
      setError(formatError(e.response?.data?.detail));
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-[#050505] px-6 md:px-12 py-24 hero-grid-bg" data-testid="login-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-md"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-6">
          Licensee Access
        </p>
        <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
          {mode === "login" ? "Sign in." : "Enlist."}
        </h1>

        <div className="mt-8 flex border border-white/10" data-testid="auth-mode-toggle">
          {["login", "register"].map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-3 text-xs font-bold uppercase tracking-[0.2em] transition-colors duration-200 ${
                mode === m ? "bg-white text-black" : "text-zinc-500 hover:text-white"
              }`}
              data-testid={`auth-mode-${m}-button`}
            >
              {m === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        <div className="mt-8 space-y-4">
          {mode === "register" && (
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Desk / fund name"
              className="w-full bg-black/40 border border-white/15 px-5 py-4 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
              data-testid="register-name-input"
            />
          )}
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full bg-black/40 border border-white/15 px-5 py-4 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
            data-testid="auth-email-input"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="Password"
            className="w-full bg-black/40 border border-white/15 px-5 py-4 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
            data-testid="auth-password-input"
          />
          {error && (
            <p className="text-[#FF3333] text-xs uppercase tracking-wider" data-testid="auth-error-message">
              {error}
            </p>
          )}
          <button
            onClick={submit}
            disabled={loading}
            className="w-full bg-white text-black font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
            data-testid="auth-submit-button"
          >
            {loading ? "…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </div>

        <Link
          to="/"
          className="mt-10 inline-block text-xs uppercase tracking-[0.2em] text-zinc-500 hover:text-white transition-colors duration-200"
          data-testid="login-return-home-link"
        >
          ← Return to Sovereign Quant
        </Link>
      </motion.div>
    </main>
  );
}
