import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Copy } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    if (user === false) navigate("/login");
  }, [user, navigate]);

  useEffect(() => {
    if (!user) return;
    axios
      .get(`${API}/me/overview`, { withCredentials: true })
      .then((r) => setData(r.data))
      .catch(() => toast.error("FAILED TO LOAD DASHBOARD"));
  }, [user]);

  const copy = async (text, label) => {
    await navigator.clipboard.writeText(text);
    toast.success(label);
  };

  if (!user || !data) {
    return (
      <main className="min-h-screen bg-[#050505] flex items-center justify-center" data-testid="dashboard-loading">
        <p className="text-xs uppercase tracking-[0.3em] text-zinc-500 animate-pulse">Loading terminal…</p>
      </main>
    );
  }

  const referralLink = `${window.location.origin}/?ref=${data.referral.code}`;

  return (
    <main className="min-h-screen bg-[#050505] px-6 md:px-12 py-24" data-testid="dashboard-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-5xl"
      >
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-4">
              Licensee Terminal
            </p>
            <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
              {data.user.name || "Operator"}
            </h1>
            <p className="mt-2 text-xs text-zinc-500 font-mono">{data.user.email}</p>
          </div>
          <button
            onClick={async () => { await logout(); navigate("/"); }}
            className="border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-6 py-3 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="dashboard-logout-button"
          >
            Sign Out
          </button>
        </div>

        <section className="mt-14" data-testid="dashboard-licences-section">
          <h2 className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">Your Licences</h2>
          {data.licences.length === 0 ? (
            <div className="border border-white/10 bg-[#0A0A0A] p-6 text-sm text-zinc-400">
              No paid licences tied to this email yet.{" "}
              <Link to="/" className="text-[#FF3333]">Acquire one</Link> with this email at checkout.
            </div>
          ) : (
            <div className="space-y-4">
              {data.licences.map((lic, i) => (
                <div key={lic.session_id} className="border border-white/10 bg-[#0A0A0A] p-5" data-testid={`licence-card-${i}`}>
                  <div className="flex justify-between items-center flex-wrap gap-2">
                    <span className="font-display uppercase text-lg">{lic.tier}</span>
                    <span className="text-[10px] uppercase tracking-[0.2em] text-[#00FF66]">Active</span>
                  </div>
                  <code className="block mt-3 break-all text-xs text-zinc-400 leading-relaxed">{lic.licence_key}</code>
                  <div className="mt-4 flex gap-3 flex-wrap">
                    <button
                      onClick={() => copy(lic.licence_key, "LICENCE KEY COPIED")}
                      className="flex items-center gap-2 bg-white text-black text-[10px] font-bold uppercase tracking-wider px-4 py-2 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                      data-testid={`licence-copy-button-${i}`}
                    >
                      <Copy className="h-3 w-3" /> Copy Key
                    </button>
                    <a
                      href={`${API}/download/${lic.session_id}`}
                      className="flex items-center gap-2 bg-[#FF3333] text-white text-[10px] font-bold uppercase tracking-wider px-4 py-2 hover:bg-red-700 active:scale-95 transition-[background-color,transform] duration-200"
                      data-testid={`licence-download-button-${i}`}
                    >
                      Download Workstation
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-14" data-testid="dashboard-orders-section">
          <h2 className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">Order History</h2>
          {data.orders.length === 0 ? (
            <p className="border border-white/10 bg-[#0A0A0A] p-6 text-sm text-zinc-500">No orders on this email yet.</p>
          ) : (
            <div className="border border-white/10">
              <div className="grid grid-cols-12 gap-2 border-b border-white/10 px-4 py-3 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
                <span className="col-span-3">Tier</span>
                <span className="col-span-3">Amount</span>
                <span className="col-span-3">Status</span>
                <span className="col-span-3 text-right">Date</span>
              </div>
              {data.orders.map((o, i) => (
                <div key={o.session_id} className="grid grid-cols-12 gap-2 px-4 py-4 text-xs border-b border-white/5" data-testid={`order-row-${i}`}>
                  <span className="col-span-3 text-[#F5F5F0]">{o.tier || "—"}</span>
                  <span className="col-span-3 tabular text-zinc-300">
                    {o.amount != null ? `$${o.amount.toLocaleString()} ${String(o.currency || "").toUpperCase()}` : "—"}
                  </span>
                  <span className={`col-span-3 uppercase tracking-wider ${
                    o.payment_status === "paid" ? "text-[#00FF66]" : o.payment_status === "refunded" ? "text-[#FF3333]" : "text-zinc-500"
                  }`}>
                    {o.payment_status}{o.revoked ? " / revoked" : ""}{o.has_key ? " / key active" : ""}
                  </span>
                  <span className="col-span-3 text-right text-zinc-500 tabular">
                    {o.created_at ? new Date(o.created_at).toLocaleDateString() : "—"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="mt-14" data-testid="dashboard-referral-section">
          <h2 className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">
            Referral Program — 2.5% Rebate
          </h2>
          <div className="border border-[#FF3333]/40 bg-[#0A0A0A] p-6">
            <p className="text-sm text-zinc-400 leading-relaxed">
              Share your link. Every month, you earn{" "}
              <span className="text-[#F5F5F0]">2.5% of everything your referrals spend</span>{" "}
              with Sovereign Quant. Rebates are credited monthly and paid out by our desk.
            </p>
            <div className="mt-5 flex gap-3 flex-wrap">
              <code className="flex-1 min-w-0 break-all border border-white/10 bg-black/40 px-4 py-3 text-xs text-zinc-300" data-testid="referral-link-text">
                {referralLink}
              </code>
              <button
                onClick={() => copy(referralLink, "REFERRAL LINK COPIED")}
                className="bg-white text-black text-[10px] font-bold uppercase tracking-wider px-5 py-3 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                data-testid="referral-copy-button"
              >
                Copy Link
              </button>
            </div>
            <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border border-white/10 text-xs uppercase tracking-[0.15em]">
              {[
                ["Your Code", data.referral.code],
                ["Referred Sales", data.referral.referred_count],
                ["Spend This Month", `$${data.referral.month_spend.toLocaleString()}`],
                ["Rebate This Month", `$${data.referral.month_rebate.toFixed(2)}`],
              ].map(([k, v]) => (
                <div key={k} className="bg-[#0A0A0A] p-4">
                  <p className="text-zinc-600">{k}</p>
                  <p className="mt-1 text-[#F5F5F0] tabular">{v}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-[10px] uppercase tracking-[0.2em] text-zinc-600">
              Lifetime referred spend: ${data.referral.lifetime_spend.toLocaleString()} // Lifetime rebate: ${data.referral.lifetime_rebate.toFixed(2)}
            </p>
            {data.referral.paid_months?.includes(data.referral.month) && (
              <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-[#00FF66]" data-testid="rebate-paid-tag">
                This month's rebate has been marked as paid
              </p>
            )}
            {data.referral.payouts?.length > 0 && (
              <p className="mt-2 text-[10px] uppercase tracking-[0.2em] text-zinc-600" data-testid="rebate-payout-history">
                Payout history: {data.referral.payouts.map((p) => `${p.month} $${p.amount.toFixed(2)}`).join(" // ")}
              </p>
            )}
          </div>
        </section>

        <div className="mt-14 flex gap-4 flex-wrap">
          <Link
            to="/guide"
            className="bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="dashboard-guide-link"
          >
            Open Setup Guide
          </Link>
          <Link
            to="/"
            className="border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="dashboard-home-link"
          >
            Return to Site
          </Link>
        </div>
      </motion.div>
    </main>
  );
}
