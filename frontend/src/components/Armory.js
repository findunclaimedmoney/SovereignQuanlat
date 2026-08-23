import { useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EASE = [0.76, 0, 0.24, 1];

const PACKS = [
  {
    lookupKey: "pack_vol_harvester",
    name: "Volatility Harvester",
    price: 149,
    tag: "Vol-targeted momentum",
    features: ["ATR regime classifier", "Inverse-vol position sizing", "Harvestable vs spike regime gating"],
  },
  {
    lookupKey: "pack_mean_reversion_pro",
    name: "Mean Reversion Pro",
    price: 149,
    tag: "Disciplined fading",
    features: ["Bollinger z-score entries", "RSI(2) confirmation", "OU half-life + 200-SMA regime filter"],
  },
  {
    lookupKey: "pack_execution_suite",
    name: "Execution Suite",
    price: 249,
    tag: "Institutional fills",
    features: ["TWAP order slicing", "Participation-rate limiter", "Square-root slippage model"],
  },
];

export const Armory = () => {
  const [selected, setSelected] = useState(null);
  const [buyer, setBuyer] = useState("");
  const [loading, setLoading] = useState(false);

  const startCheckout = async () => {
    if (buyer.trim().length < 2) {
      toast.error("ENTER A NAME FOR THE PURCHASE RECORD");
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/payments/checkout`, {
        lookup_key: selected.lookupKey,
        licensee_name: buyer.trim(),
        origin_url: window.location.origin,
        referral_code: localStorage.getItem("sq_ref") || null,
      });
      window.location.href = data.checkout_url;
    } catch {
      toast.error("CHECKOUT FAULT — PLEASE RETRY");
      setLoading(false);
    }
  };

  return (
    <section id="armory" className="px-6 md:px-12 py-32 border-t border-white/10" data-testid="armory-section">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mb-16"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          The Armory
        </p>
        <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black">
          Strategy <span className="text-outline">packs.</span>
        </h2>
        <p className="mt-6 max-w-xl text-base md:text-lg text-zinc-400">
          One-time drop-in modules for your workstation. Own the code outright —
          no subscription, no lock-in. Delivered instantly after checkout.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {PACKS.map((pack, i) => (
          <motion.div
            key={pack.lookupKey}
            initial={{ opacity: 0, y: 60 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.9, delay: i * 0.12, ease: EASE }}
            whileHover={{ y: -8 }}
            className="flex flex-col border border-white/10 bg-[#151B24] p-8 hover:border-white/25 transition-[border-color,transform] duration-300"
            data-testid={`pack-card-${pack.lookupKey}`}
          >
            <p className="text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">{pack.tag}</p>
            <h3 className="font-display text-xl md:text-2xl font-light uppercase mt-3">{pack.name}</h3>
            <p className="font-display text-3xl font-black tabular mt-6">
              ${pack.price}
              <span className="text-sm text-zinc-500 font-light"> one-time</span>
            </p>
            <ul className="mt-6 space-y-3 text-sm flex-1">
              {pack.features.map((f, j) => (
                <li key={j} className="flex items-start gap-3 text-zinc-300">
                  <span className="text-[#10B981] mt-0.5">+</span> {f}
                </li>
              ))}
            </ul>
            <button
              onClick={() => {
                setSelected(pack);
                setBuyer("");
              }}
              className="mt-8 w-full border border-white/20 text-white font-bold uppercase tracking-wider px-6 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
              data-testid={`buy-${pack.lookupKey}-button`}
            >
              Acquire Pack
            </button>
          </motion.div>
        ))}
      </div>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="bg-[#111827] border border-white/10 rounded-none text-[#E5E7EB] sm:max-w-md" data-testid="pack-checkout-dialog">
          <DialogHeader>
            <DialogTitle className="font-display uppercase tracking-tight text-xl">
              {selected?.name}
            </DialogTitle>
            <DialogDescription className="text-zinc-500 text-sm">
              One-time purchase. The module zip is delivered instantly after payment — and to your email.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <label className="text-xs uppercase tracking-[0.2em] text-zinc-500">Buyer Name</label>
            <Input
              value={buyer}
              onChange={(e) => setBuyer(e.target.value)}
              placeholder="e.g. Aurelius Capital LLC"
              className="rounded-none bg-black/40 border-white/15 font-mono"
              data-testid="pack-buyer-name-input"
            />
            <button
              onClick={startCheckout}
              disabled={loading}
              className="w-full bg-[#3B82F6] text-white font-bold uppercase tracking-wider px-8 py-4 hover:bg-blue-600 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
              data-testid="pack-checkout-submit-button"
            >
              {loading ? "Routing to Secure Checkout…" : `Proceed — $${selected?.price} one-time`}
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
};
