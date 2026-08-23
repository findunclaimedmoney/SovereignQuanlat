import { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Admin() {
  const [key, setKey] = useState(localStorage.getItem("sq_admin_key") || "");
  const [orders, setOrders] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/admin/orders`, { headers: { "X-Admin-Key": key } });
      setOrders(data.orders);
      localStorage.setItem("sq_admin_key", key);
    } catch (e) {
      toast.error(e.response?.status === 429 ? "LOCKED OUT — 15 MIN" : "INVALID ADMIN KEY");
      setOrders(null);
    }
    setLoading(false);
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
      </motion.div>
    </main>
  );
}
