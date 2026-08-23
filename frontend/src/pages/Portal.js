import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { motion } from "framer-motion";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Portal() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!email.includes("@")) return;
    setLoading(true);
    try {
      await axios.post(`${API}/portal/recover`, { email });
    } catch {
      /* generic response regardless */
    }
    setSent(true);
    setLoading(false);
  };

  return (
    <main
      className="min-h-screen bg-[#0B0F14] text-[#E5E7EB] flex flex-col items-center justify-center px-5 py-10"
      style={{ fontFamily: "'DM Sans', system-ui, sans-serif" }}
      data-testid="portal-page"
    >
      <motion.header
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8 }}
        className="absolute top-7 left-6 md:left-10 flex items-center gap-3"
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
          Buyer Portal
        </p>
        <h1 className="font-serif-display text-[44px] leading-[1.1] text-white mb-7">
          Recover your keys<em className="text-[#F59E0B] italic">.</em>
        </h1>
        <p className="text-[15px] leading-relaxed text-[#9CA3AF] mb-7">
          Enter the email you used at checkout. Every licence key registered to
          it — plus fresh download links — lands in your inbox within a minute.
        </p>

        {!sent ? (
          <div>
            <label className="block text-[13px] text-[#9CA3AF] mb-1.5">Purchase email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="you@example.com"
              className="w-full px-3.5 py-[13px] rounded-[10px] border border-white/[0.08] bg-[#151B24] text-[#E5E7EB] text-[15px] outline-none focus:border-[#3B82F6] transition-colors duration-200 placeholder:text-[#6B7280] mb-[18px]"
              data-testid="portal-email-input"
            />
            <button
              onClick={submit}
              disabled={loading}
              className="w-full py-3.5 rounded-[10px] bg-[#3B82F6] text-white font-semibold text-[15px] hover:opacity-90 active:scale-[0.98] disabled:opacity-50 transition-[opacity,transform] duration-150"
              data-testid="portal-submit-button"
            >
              {loading ? "Transmitting…" : "Email My Licence Keys"}
            </button>
          </div>
        ) : (
          <div
            className="rounded-[10px] border border-white/[0.08] bg-[#111827] p-5"
            data-testid="portal-confirmation"
          >
            <p className="text-sm text-[#E5E7EB] leading-relaxed">
              <span className="text-[#10B981] font-semibold">Sent.</span> If a
              purchase exists for this address, your keys are en route. Check
              spam if nothing arrives in five minutes.
            </p>
          </div>
        )}

        <p className="mt-[22px] text-xs text-[#9CA3AF] text-center">
          Keys are only ever sent to the purchase address.
        </p>
      </motion.div>

      <Link
        to="/"
        className="mt-10 text-[13px] text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors duration-200 no-underline"
        data-testid="portal-return-home-link"
      >
        ← Return to Sovereign Quant
      </Link>
    </main>
  );
}
