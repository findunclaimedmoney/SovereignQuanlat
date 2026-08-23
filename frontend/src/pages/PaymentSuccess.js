import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Copy, Check } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState({ phase: "polling" });
  const [copied, setCopied] = useState(false);
  const [upgrading, setUpgrading] = useState(false);

  const upgrade = async () => {
    setUpgrading(true);
    try {
      const { data } = await axios.post(`${API}/upgrades`, { session_id: sessionId });
      if (data.status === "upgraded") {
        toast.success("UPGRADED TO INSTITUTIONAL — NEW KEY ISSUED");
        const order = await axios.get(`${API}/orders/${sessionId}`);
        setState({ phase: "paid", order: order.data });
      } else {
        toast.info("PRORATION INVOICE ISSUED — KEY UPGRADES AFTER PAYMENT");
      }
    } catch (e) {
      const d = e.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "UPGRADE FAILED");
    }
    setUpgrading(false);
  };

  useEffect(() => {
    if (!sessionId) {
      setState({ phase: "error" });
      return undefined;
    }
    let attempts = 0;
    let timer;
    const poll = async () => {
      try {
        const { data } = await axios.get(`${API}/payments/status/${sessionId}`);
        if (data.payment_status === "paid") {
          const order = await axios.get(`${API}/orders/${sessionId}`);
          setState({ phase: "paid", order: order.data });
          return;
        }
      } catch {
        /* keep polling */
      }
      attempts += 1;
      if (attempts < 30) {
        timer = setTimeout(poll, 2000);
      } else {
        setState({ phase: "timeout" });
      }
    };
    poll();
    return () => clearTimeout(timer);
  }, [sessionId]);

  const copyKey = async () => {
    await navigator.clipboard.writeText(state.order.licence_key);
    setCopied(true);
    toast.success("LICENCE KEY COPIED TO CLIPBOARD");
    setTimeout(() => setCopied(false), 2000);
  };

  const order = state.order;

  return (
    <main className="min-h-screen bg-[#0B0F14] px-6 md:px-12 py-24 hero-grid-bg" data-testid="payment-success-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-3xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          Fulfilment Terminal
        </p>

        {state.phase === "polling" && (
          <div data-testid="payment-polling-state">
            <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
              Confirming payment<span className="animate-pulse">…</span>
            </h1>
            <p className="mt-6 text-zinc-400 text-sm leading-relaxed">
              Handshaking with the payment network. Your cryptographic licence
              is signed the moment settlement clears.
            </p>
          </div>
        )}

        {state.phase === "paid" && order && (
          <div data-testid="payment-confirmed-state">
            <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
              {order.licence_key ? (
                <>Licence <span className="text-[#10B981]">issued.</span></>
              ) : order.pack_name ? (
                <>Pack <span className="text-[#10B981]">unlocked.</span></>
              ) : (
                <>Coach <span className="text-[#10B981]">activated.</span></>
              )}
            </h1>
            <p className="mt-6 text-zinc-400 text-sm leading-relaxed max-w-xl">
              {order.licence_key ? (
                <>
                  Paste this key into the workstation sidebar under{" "}
                  <span className="text-[#E5E7EB]">Activate New Licence Key</span>.
                  Activation is fully offline — guard this key like capital.
                </>
              ) : order.pack_name ? (
                "Your strategy module is ready. Download it below and drop the .py file into your workstation folder."
              ) : (
                "ATLAS is live. Open your dashboard, scroll to the AI Coach panel, and start your first session."
              )}
            </p>

            {order.licence_key && (
            <>
            <div className="mt-10 border border-white/10 bg-[#111827]">
              <div className="flex items-center justify-between border-b border-white/10 px-5 py-3 text-[10px] uppercase tracking-[0.25em] text-zinc-500">
                <span>HMAC-SHA256 // Offline Key</span>
                <span className="text-[#10B981]">Signature Valid</span>
              </div>
              <div className="p-5">
                <code
                  className="block break-all text-xs leading-relaxed text-zinc-300"
                  data-testid="licence-key-text"
                >
                  {order.licence_key}
                </code>
                <div className="mt-5 flex flex-wrap gap-3">
                  <button
                    onClick={copyKey}
                    className="flex items-center gap-2 bg-white text-black text-xs font-bold uppercase tracking-wider px-6 py-3 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                    data-testid="copy-licence-key-button"
                  >
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    {copied ? "Copied" : "Copy Key"}
                  </button>
                  <a
                    href={`${API}/download/${sessionId}`}
                    className="flex items-center gap-2 bg-[#3B82F6] text-white text-xs font-bold uppercase tracking-wider px-6 py-3 hover:bg-blue-600 active:scale-95 transition-[background-color,transform] duration-200"
                    data-testid="download-workstation-button"
                  >
                    Download Workstation
                  </a>
                </div>
              </div>
            </div>

            <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border border-white/10 text-xs uppercase tracking-[0.15em]" data-testid="order-details-grid">
              {[
                ["Tier", order.tier],
                ["Licensee", order.licensee],
                ["Duration", `${order.duration_days} days`],
                ["Max Capital", `$${(order.max_capital || 0).toLocaleString()}`],
              ].map(([k, v]) => (
                <div key={k} className="bg-[#111827] p-4">
                  <p className="text-zinc-600">{k}</p>
                  <p className="mt-1 text-[#E5E7EB] break-words">{v}</p>
                </div>
              ))}
            </div>

            {order.tier === "Professional" && (
              <button
                onClick={upgrade}
                disabled={upgrading}
                className="mt-6 border border-[#F59E0B]/60 text-[#F59E0B] text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-[#F59E0B]/10 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
                data-testid="upgrade-to-institutional-button"
              >
                {upgrading ? "Upgrading…" : "Upgrade to Institutional — Prorated"}
              </button>
            )}
            </>
            )}

            {order.pack_name && (
              <div className="mt-10 border border-white/10 bg-[#111827]">
                <div className="flex items-center justify-between border-b border-white/10 px-5 py-3 text-[10px] uppercase tracking-[0.25em] text-zinc-500">
                  <span>Strategy Pack // {order.pack_name}</span>
                  <span className="text-[#10B981]">Ready</span>
                </div>
                <div className="p-5">
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Drop-in module for the Sovereign Quant workstation. One-time
                    purchase — the code is yours.
                  </p>
                  <a
                    href={`${API}/download/pack/${sessionId}`}
                    className="mt-5 inline-flex items-center gap-2 bg-[#3B82F6] text-white text-xs font-bold uppercase tracking-wider px-6 py-3 hover:bg-blue-600 active:scale-95 transition-[background-color,transform] duration-200"
                    data-testid="download-pack-button"
                  >
                    Download {order.pack_name}
                  </a>
                </div>
              </div>
            )}

            {!order.licence_key && !order.pack_name && (
              <div className="mt-10 border border-white/10 bg-[#111827] p-6" data-testid="coach-active-card">
                <p className="text-sm text-zinc-300 leading-relaxed">
                  <span className="text-[#10B981]">ACTIVE.</span> Sign in with this
                  purchase email and your AI Coach panel unlocks automatically.
                </p>
                <Link
                  to="/dashboard"
                  className="mt-5 inline-block bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                  data-testid="coach-dashboard-link"
                >
                  Open Dashboard
                </Link>
              </div>
            )}
          </div>
        )}

        {(state.phase === "timeout" || state.phase === "error") && (
          <div data-testid="payment-error-state">
            <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
              Signal <span className="text-[#F59E0B]">lost.</span>
            </h1>
            <p className="mt-6 text-zinc-400 text-sm leading-relaxed max-w-xl">
              We could not confirm this session. If your card was charged, your
              licence is still issued — contact support with your receipt.
            </p>
          </div>
        )}

        <Link
          to="/"
          className="mt-14 inline-block border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
          data-testid="return-home-link"
        >
          Return to Sovereign Quant
        </Link>
      </motion.div>
    </main>
  );
}
