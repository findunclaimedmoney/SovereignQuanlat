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
    <main className="min-h-screen bg-[#050505] px-6 md:px-12 py-24 hero-grid-bg" data-testid="portal-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-6">
          Buyer Portal
        </p>
        <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
          Recover your <span className="text-outline">keys.</span>
        </h1>
        <p className="mt-6 text-zinc-400 text-sm leading-relaxed">
          Enter the email you used at checkout. Every licence key registered to
          it — plus fresh download links — lands in your inbox within a minute.
        </p>

        {!sent ? (
          <div className="mt-10 space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="you@yourfund.com"
              className="w-full bg-black/40 border border-white/15 px-5 py-4 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
              data-testid="portal-email-input"
            />
            <button
              onClick={submit}
              disabled={loading}
              className="w-full bg-white text-black font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
              data-testid="portal-submit-button"
            >
              {loading ? "Transmitting…" : "Email My Licence Keys"}
            </button>
          </div>
        ) : (
          <div className="mt-10 border border-white/10 bg-[#0A0A0A] p-6" data-testid="portal-confirmation">
            <p className="text-sm text-zinc-300 leading-relaxed">
              <span className="text-[#00FF66]">SENT.</span> If a purchase exists
              for this address, your keys are en route. Check spam if nothing
              arrives in five minutes.
            </p>
          </div>
        )}

        <Link
          to="/"
          className="mt-14 inline-block border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
          data-testid="portal-return-home-link"
        >
          Return to Sovereign Quant
        </Link>
      </motion.div>
    </main>
  );
}
