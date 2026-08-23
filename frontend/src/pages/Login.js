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
    <main
      className="min-h-screen bg-[#0B0F14] text-[#E5E7EB] flex flex-col items-center justify-center px-5 py-10"
      style={{ fontFamily: "'DM Sans', system-ui, sans-serif" }}
      data-testid="login-page"
    >
      <motion.header
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="absolute top-7 left-6 md:left-10 flex items-center gap-3"
        data-testid="login-brand"
      >
        <img src="/sq-logo.png" alt="Sovereign Quant logo" className="h-8 w-8 object-contain" />
        <span className="font-serif-display text-[22px] text-[#9CA3AF] tracking-wide">
          Sovereign Quant
        </span>
      </motion.header>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-[420px]"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-[#F59E0B] mb-3.5">
          Licensee Access
        </p>
        <h1 className="font-serif-display text-[44px] leading-[1.1] text-white mb-7">
          {mode === "login" ? (
            <>Sign in<em className="text-[#F59E0B] italic">.</em></>
          ) : (
            <>Enlist<em className="text-[#F59E0B] italic">.</em></>
          )}
        </h1>

        <div
          className="flex border border-white/[0.08] rounded-[10px] overflow-hidden mb-6"
          data-testid="auth-mode-toggle"
        >
          {[
            ["login", "Sign In"],
            ["register", "Create Account"],
          ].map(([m, label]) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-3 text-sm font-semibold transition-colors duration-200 ${
                mode === m ? "bg-[#3B82F6] text-white" : "text-[#9CA3AF] hover:text-white"
              }`}
              data-testid={`auth-mode-${m}-button`}
            >
              {label}
            </button>
          ))}
        </div>

        <div>
          {mode === "register" && (
            <>
              <label className="block text-[13px] text-[#9CA3AF] mb-1.5">Desk / fund name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Aurelius Capital LLC"
                className="w-full px-3.5 py-[13px] mb-4.5 rounded-[10px] border border-white/[0.08] bg-[#151B24] text-[#E5E7EB] text-[15px] outline-none focus:border-[#3B82F6] transition-colors duration-200 placeholder:text-[#6B7280] mb-[18px]"
                data-testid="register-name-input"
              />
            </>
          )}
          <label className="block text-[13px] text-[#9CA3AF] mb-1.5">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3.5 py-[13px] rounded-[10px] border border-white/[0.08] bg-[#151B24] text-[#E5E7EB] text-[15px] outline-none focus:border-[#3B82F6] transition-colors duration-200 placeholder:text-[#6B7280] mb-[18px]"
            data-testid="auth-email-input"
          />
          <label className="block text-[13px] text-[#9CA3AF] mb-1.5">Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            placeholder="••••••••"
            className="w-full px-3.5 py-[13px] rounded-[10px] border border-white/[0.08] bg-[#151B24] text-[#E5E7EB] text-[15px] outline-none focus:border-[#3B82F6] transition-colors duration-200 placeholder:text-[#6B7280] mb-[18px]"
            data-testid="auth-password-input"
          />
          {error && (
            <p className="text-[#F87171] text-[13px] mb-4" data-testid="auth-error-message">
              {error}
            </p>
          )}
          <button
            onClick={submit}
            disabled={loading}
            className="w-full py-3.5 rounded-[10px] bg-[#3B82F6] text-white font-semibold text-[15px] hover:opacity-90 active:scale-[0.98] disabled:opacity-50 transition-[opacity,transform] duration-150"
            data-testid="auth-submit-button"
          >
            {loading ? "…" : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </div>

        <p className="mt-[22px] text-xs text-[#9CA3AF] text-center">
          Software licensing only. Not investment advice.
        </p>
      </motion.div>

      <Link
        to="/"
        className="mt-10 text-[13px] text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors duration-200 no-underline"
        data-testid="login-return-home-link"
      >
        ← Return to Sovereign Quant
      </Link>
    </main>
  );
}
