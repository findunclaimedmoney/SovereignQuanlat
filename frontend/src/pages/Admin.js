import { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Admin() {
  const [key, setKey] = useState(localStorage.getItem("sq_admin_key") || "");
  const [orders, setOrders] = useState(null);
  const [rebates, setRebates] = useState([]);
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [siteName, setSiteName] = useState("");
  const [siteInstructions, setSiteInstructions] = useState("");
  const [generating, setGenerating] = useState(false);

  const headers = { "X-Admin-Key": key };

  const load = async () => {
    setLoading(true);
    try {
      const [o, r, s] = await Promise.all([
        axios.get(`${API}/admin/orders`, { headers }),
        axios.get(`${API}/admin/rebates`, { headers }),
        axios.get(`${API}/admin/sites`, { headers }),
      ]);
      setOrders(o.data.orders);
      setRebates(r.data.rebates);
      setSites(s.data.sites);
      localStorage.setItem("sq_admin_key", key);
    } catch (e) {
      toast.error(e.response?.status === 429 ? "LOCKED OUT — 15 MIN" : "INVALID ADMIN KEY");
      setOrders(null);
    }
    setLoading(false);
  };

  const payRebate = async (r) => {
    if (!window.confirm(`Mark ${r.code} ${r.month} rebate of $${r.month_rebate} as paid?`)) return;
    try {
      await axios.post(`${API}/admin/rebates/pay`,
        { code: r.code, month: r.month, amount: r.month_rebate }, { headers });
      toast.success("REBATE MARKED PAID");
      load();
    } catch {
      toast.error("PAYOUT MARK FAILED");
    }
  };

  const generateSite = async () => {
    if (siteName.trim().length < 2 || siteInstructions.trim().length < 10) {
      toast.error("NAME + INSTRUCTIONS REQUIRED");
      return;
    }
    setGenerating(true);
    try {
      await axios.post(`${API}/admin/sites/generate`,
        { name: siteName.trim(), instructions: siteInstructions.trim() }, { headers });
      toast.success("FORGE STARTED — SELF-REVIEW RUNS IN BACKGROUND");
      setSiteName("");
      setSiteInstructions("");
      const t0 = Date.now();
      const poll = setInterval(async () => {
        try {
          const { data } = await axios.get(`${API}/admin/sites`, { headers });
          setSites(data.sites);
          if (!data.sites.some((s) => s.status === "generating") || Date.now() - t0 > 240000) {
            clearInterval(poll);
            setGenerating(false);
          }
        } catch {
          /* keep polling */
        }
      }, 5000);
    } catch {
      toast.error("FORGE FAILED TO START");
      setGenerating(false);
    }
  };

  const downloadSite = async (siteId) => {
    try {
      const res = await axios.get(`${API}/admin/sites/${siteId}/download`, {
        headers, responseType: "blob",
      });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `sovereign-site-${siteId.slice(0, 8)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("DOWNLOAD FAILED");
    }
  };

  const refund = async (sessionId) => {
    if (!window.confirm("Refund this order, cancel its subscription, and revoke the licence record?")) return;
    try {
      await axios.post(`${API}/admin/orders/${sessionId}/refund`, {}, { headers: { "X-Admin-Key": key } });
      toast.success("REFUNDED — LICENCE REVOKED");
      load();
    } catch (e) {
      const d = e.response?.data?.detail;
      toast.error(typeof d === "string" ? d : "REFUND FAILED");
    }
  };

  return (
    <main className="min-h-screen bg-[#050505] px-6 md:px-12 py-24" data-testid="admin-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-5xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-6">
          Sovereign Quant // Internal
        </p>
        <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
          Refund <span className="text-outline">console.</span>
        </h1>

        <div className="mt-10 flex gap-3">
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="Admin key"
            className="flex-1 bg-black/40 border border-white/15 px-5 py-4 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
            data-testid="admin-key-input"
          />
          <button
            onClick={load}
            disabled={loading}
            className="bg-white text-black text-xs font-bold uppercase tracking-wider px-8 hover:bg-zinc-200 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
            data-testid="admin-load-button"
          >
            {loading ? "…" : "Load Orders"}
          </button>
        </div>

        {orders && (
          <div className="mt-10 border border-white/10" data-testid="admin-orders-table">
            <div className="grid grid-cols-12 gap-2 border-b border-white/10 px-4 py-3 text-[10px] uppercase tracking-[0.2em] text-zinc-500">
              <span className="col-span-3">Licensee</span>
              <span className="col-span-2">Tier</span>
              <span className="col-span-2">Amount</span>
              <span className="col-span-2">Status</span>
              <span className="col-span-3 text-right">Action</span>
            </div>
            {orders.length === 0 && (
              <p className="px-4 py-8 text-sm text-zinc-500">No orders yet.</p>
            )}
            {orders.map((o, i) => (
              <div
                key={o.session_id}
                className="grid grid-cols-12 gap-2 items-center border-b border-white/5 px-4 py-4 text-xs"
                data-testid={`admin-order-row-${i}`}
              >
                <div className="col-span-3">
                  <p className="text-[#F5F5F0] truncate">{o.licensee_name || "—"}</p>
                  <p className="text-zinc-600 truncate">{o.licence_email_to || "no email"}</p>
                </div>
                <span className="col-span-2 text-zinc-300">{o.tier || o.lookup_key || "—"}</span>
                <span className="col-span-2 tabular text-zinc-300">
                  {o.amount != null ? `$${o.amount.toLocaleString()} ${String(o.currency || "").toUpperCase()}` : "—"}
                </span>
                <span
                  className={`col-span-2 uppercase tracking-wider ${
                    o.payment_status === "paid"
                      ? "text-[#00FF66]"
                      : o.payment_status === "refunded"
                        ? "text-[#FF3333]"
                        : "text-zinc-500"
                  }`}
                >
                  {o.payment_status}
                  {o.licence_revoked && " / revoked"}
                </span>
                <div className="col-span-3 text-right">
                  {o.payment_status === "paid" && (
                    <button
                      onClick={() => refund(o.session_id)}
                      className="bg-[#FF3333] text-white text-[10px] font-bold uppercase tracking-wider px-4 py-2 hover:bg-red-700 active:scale-95 transition-[background-color,transform] duration-200"
                      data-testid={`refund-button-${i}`}
                    >
                      Refund + Revoke
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {orders && (
          <>
            <section className="mt-14" data-testid="admin-rebates-section">
              <h2 className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">
                Referral Rebates — 2.5% Monthly
              </h2>
              {rebates.length === 0 ? (
                <p className="border border-white/10 bg-[#0A0A0A] p-6 text-sm text-zinc-500">No referred sales yet.</p>
              ) : (
                <div className="space-y-3">
                  {rebates.map((r, i) => (
                    <div key={r.code} className="flex items-center justify-between border border-white/10 bg-[#0A0A0A] px-5 py-4 text-xs" data-testid={`rebate-row-${i}`}>
                      <div>
                        <p className="text-[#F5F5F0] font-bold">{r.code}</p>
                        <p className="text-zinc-500 mt-1">
                          {r.referred_count} sales // ${r.month_spend.toLocaleString()} this month // ${r.lifetime_spend.toLocaleString()} lifetime
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="tabular text-[#F5F5F0]">${r.month_rebate.toFixed(2)} / {r.month}</p>
                        {r.month_paid ? (
                          <p className="text-[#00FF66] uppercase tracking-wider mt-1">Paid</p>
                        ) : (
                          <button
                            onClick={() => payRebate(r)}
                            className="mt-2 bg-white text-black text-[10px] font-bold uppercase tracking-wider px-4 py-2 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                            data-testid={`rebate-pay-button-${i}`}
                          >
                            Mark Paid
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="mt-14" data-testid="admin-foundry-section">
              <h2 className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">
                Site Foundry — Sovereign Ecosystem Generator
              </h2>
              <div className="border border-white/10 bg-[#0A0A0A] p-6 space-y-4">
                <input
                  value={siteName}
                  onChange={(e) => setSiteName(e.target.value)}
                  placeholder="Project name — e.g. Licence Docs Portal"
                  className="w-full bg-black/40 border border-white/15 px-5 py-3 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
                  data-testid="foundry-name-input"
                />
                <textarea
                  value={siteInstructions}
                  onChange={(e) => setSiteInstructions(e.target.value)}
                  placeholder="Instructions — what to build, sections, content, tone…"
                  rows={4}
                  className="w-full bg-black/40 border border-white/15 px-5 py-3 text-sm font-mono outline-none focus:border-[#FF3333]/60 transition-colors duration-200 placeholder:text-zinc-600"
                  data-testid="foundry-instructions-input"
                />
                <button
                  onClick={generateSite}
                  disabled={generating}
                  className="bg-[#FF3333] text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-red-700 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
                  data-testid="foundry-generate-button"
                >
                  {generating ? "Forging… (up to ~2 min)" : "Generate Site"}
                </button>
                {sites.length > 0 && (
                  <div className="pt-4 space-y-2 border-t border-white/10">
                    {sites.map((s, i) => (
                      <div key={s.site_id} className="flex items-center justify-between text-xs" data-testid={`foundry-site-row-${i}`}>
                        <span className="text-zinc-300">
                          {s.name}{" "}
                          <span className={s.status === "ready" ? "text-zinc-600" : "text-[#FF3333] animate-pulse"}>
                            {s.status === "ready" ? `(${s.file_count} files)` : s.status === "failed" ? "(failed)" : "(forging…)"}
                          </span>
                        </span>
                        {s.status === "ready" && (
                          <button
                            onClick={() => downloadSite(s.site_id)}
                            className="text-[#FF3333] uppercase tracking-wider hover:text-red-400 transition-colors duration-200"
                            data-testid={`foundry-download-button-${i}`}
                          >
                            Download Zip
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </>
        )}
      </motion.div>
    </main>
  );
}
