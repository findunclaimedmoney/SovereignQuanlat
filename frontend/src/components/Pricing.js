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

const TIERS = [
  {
    id: "community",
    name: "Community",
    price: 0,
    lookupKey: null,
    tagline: "Evaluate the core.",
    maxCapital: "$50,000",
    strategies: "1",
    features: ["Orchestrator core", "Strategy playground", "Risk gates + kill switch"],
    locked: ["Branded reports", "Signal export", "Walk-forward"],
    dominant: false,
  },
  {
    id: "professional",
    name: "Professional",
    price: 499,
    lookupKey: "professional_annual",
    tagline: "For the self-owned desk.",
    maxCapital: "$1,000,000",
    strategies: "3",
    features: [
      "Everything in Community",
      "Walk-forward analysis",
      "Branded PDF tearsheets",
      "Signal export",
    ],
    locked: ["Monte Carlo", "Multi-account routing"],
    dominant: false,
  },
  {
    id: "institutional",
    name: "Institutional",
    price: 1999,
    lookupKey: "institutional_annual",
    tagline: "For the sovereign fund.",
    maxCapital: "$50,000,000",
    strategies: "10",
    features: [
      "Everything in Professional",
      "Monte Carlo simulation",
      "Multi-account routing",
      "Priority engineering channel",
    ],
    locked: [],
    dominant: true,
  },
];

export const Pricing = () => {
  const [selected, setSelected] = useState(null);
  const [licensee, setLicensee] = useState("");
  const [loading, setLoading] = useState(false);

  const startCheckout = async () => {
    if (licensee.trim().length < 2) {
      toast.error("ENTER A LICENSEE NAME — IT IS SIGNED INTO YOUR KEY");
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/payments/checkout`, {
        lookup_key: selected.lookupKey,
        licensee_name: licensee.trim(),
        origin_url: window.location.origin,
        referral_code: localStorage.getItem("sq_ref") || null,
      });
      window.location.href = data.checkout_url;
    } catch (e) {
      toast.error("CHECKOUT FAULT — PLEASE RETRY");
      setLoading(false);
    }
  };

  return (
    <section id="pricing" className="px-6 md:px-12 py-32 md:py-48 border-t border-white/10" data-testid="pricing-section">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mb-20"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          Licence Acquisition
        </p>
        <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black">
          Choose your <span className="text-outline-red">clearance.</span>
        </h2>
        <p className="mt-6 max-w-xl text-base md:text-lg text-zinc-400">
          Annual offline licences. Keys are Ed25519-signed, delivered instantly, and
          activated locally — the licensing server never sees your machine again.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {TIERS.map((tier, i) => (
          <motion.div
            key={tier.id}
            initial={{ opacity: 0, y: 60 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.9, delay: i * 0.12, ease: EASE }}
            whileHover={{ y: -8 }}
            className={`relative flex flex-col border p-8 md:p-10 transition-[border-color,box-shadow] duration-300 ${
              tier.dominant
                ? "bg-[#111827] border-[#F59E0B]/50 shadow-[0_0_60px_-15px_rgba(255,51,51,0.35)]"
                : "bg-[#151B24] border-white/10 hover:border-white/25"
            }`}
            data-testid={`pricing-card-${tier.id}`}
          >
            {tier.dominant && (
              <span className="absolute -top-px right-8 bg-[#3B82F6] text-white text-[10px] font-bold uppercase tracking-[0.2em] px-3 py-1">
                Most Deployed
              </span>
            )}

            <h3 className="font-display text-2xl md:text-3xl font-light uppercase">{tier.name}</h3>
            <p className="mt-2 text-xs uppercase tracking-[0.2em] text-zinc-500">{tier.tagline}</p>

            <div className="mt-8 flex items-end gap-2">
              <span className="font-display text-4xl md:text-5xl font-black tabular" data-testid={`pricing-price-${tier.id}`}>
                ${tier.price.toLocaleString()}
              </span>
              <span className="text-xs uppercase tracking-[0.2em] text-zinc-500 mb-2">
                {tier.price === 0 ? "/ forever" : "/ year"}
              </span>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-4 border-y border-white/10 py-6 text-xs uppercase tracking-[0.15em]">
              <div>
                <p className="text-zinc-500">Max Capital</p>
                <p className="mt-1 text-[#E5E7EB] tabular">{tier.maxCapital}</p>
              </div>
              <div>
                <p className="text-zinc-500">Strategies</p>
                <p className="mt-1 text-[#E5E7EB] tabular">{tier.strategies}</p>
              </div>
            </div>

            <ul className="mt-8 space-y-3 text-sm flex-1">
              {tier.features.map((f, j) => (
                <li key={j} className="flex items-start gap-3 text-zinc-300">
                  <span className="text-[#10B981] mt-0.5">+</span> {f}
                </li>
              ))}
              {tier.locked.map((f, j) => (
                <li key={j} className="flex items-start gap-3 text-zinc-600 line-through">
                  <span className="text-zinc-700 mt-0.5">—</span> {f}
                </li>
              ))}
            </ul>

            {tier.lookupKey ? (
              <button
                onClick={() => {
                  setSelected(tier);
                  setLicensee("");
                }}
                className={`mt-10 w-full font-bold uppercase tracking-wider px-8 py-4 active:scale-95 transition-[background-color,transform,color] duration-200 ${
                  tier.dominant
                    ? "bg-[#3B82F6] text-white hover:bg-blue-600"
                    : "bg-white text-black hover:bg-zinc-200"
                }`}
                data-testid={`buy-${tier.id}-button`}
              >
                Acquire {tier.name}
              </button>
            ) : (
              <button
                onClick={() =>
                  window.__lenis
                    ? window.__lenis.scrollTo("#deploy", { offset: -72 })
                    : document.querySelector("#deploy")?.scrollIntoView({ behavior: "smooth" })
                }
                className="mt-10 w-full border border-white/20 text-white font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
                data-testid="community-download-button"
              >
                Included in Download
              </button>
            )}
          </motion.div>
        ))}
      </div>

      <p className="mt-6 text-[10px] uppercase tracking-[0.15em] text-zinc-600 leading-relaxed max-w-3xl" data-testid="pricing-plain-terms">
        In plain terms — Max Capital: the largest account size the safety engine
        will manage for you, a hard technical ceiling set by your tier.
        Strategies: how many can run at the same time. Nothing here trades real
        money by itself.
      </p>

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mt-6 border border-white/10 bg-[#151B24] p-8 md:p-10 flex flex-col md:flex-row md:items-center justify-between gap-8 hover:border-[#F59E0B]/40 transition-colors duration-300"
        data-testid="pricing-card-coach"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold">Add-On</p>
          <h3 className="font-display text-2xl md:text-3xl font-light uppercase mt-3">
            AI Coach <span className="text-outline">— Atlas</span>
          </h3>
          <p className="mt-3 text-sm text-zinc-400 max-w-lg leading-relaxed">
            A Claude-Opus mentor inside your dashboard. Strategy mechanics, risk
            discipline, workstation mastery — on tap, 24/7. Software education,
            never investment advice. Cancel anytime.
          </p>
        </div>
        <div className="text-left md:text-right shrink-0">
          <p className="font-display text-3xl md:text-4xl font-black tabular" data-testid="pricing-price-coach">
            $49<span className="text-sm text-zinc-500 font-light">/mo</span>
          </p>
          <button
            onClick={() => {
              setSelected({ id: "ai_coach", name: "AI Coach", price: 49, lookupKey: "ai_coach_monthly", interval: "month" });
              setLicensee("");
            }}
            className="mt-4 border border-[#F59E0B]/60 text-[#F59E0B] font-bold uppercase tracking-wider px-8 py-4 hover:bg-[#F59E0B]/10 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="buy-coach-button"
          >
            Add AI Coach
          </button>
        </div>
      </motion.div>

      <Dialog open={!!selected} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent
          className="bg-[#111827] border border-white/10 rounded-none text-[#E5E7EB] sm:max-w-md"
          data-testid="checkout-dialog"
        >
          <DialogHeader>
            <DialogTitle className="font-display uppercase tracking-tight text-xl">
              {selected?.name} Licence
            </DialogTitle>
            <DialogDescription className="text-zinc-500 text-sm">
              The licensee name is cryptographically signed into your Ed25519 key.
              It appears inside the workstation on activation.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            <label className="text-xs uppercase tracking-[0.2em] text-zinc-500">
              Licensee Name
            </label>
            <Input
              value={licensee}
              onChange={(e) => setLicensee(e.target.value)}
              placeholder="e.g. Aurelius Capital LLC"
              className="rounded-none bg-black/40 border-white/15 font-mono"
              data-testid="licensee-name-input"
            />
            {typeof window !== "undefined" && localStorage.getItem("sq_ref") && (
              <p className="text-[10px] uppercase tracking-[0.2em] text-[#10B981]" data-testid="referral-applied-note">
                Referral {localStorage.getItem("sq_ref")} applied — your referrer earns 2.5%
              </p>
            )}
            <button
              onClick={startCheckout}
              disabled={loading}
              className="w-full bg-[#3B82F6] text-white font-bold uppercase tracking-wider px-8 py-4 hover:bg-blue-600 active:scale-95 disabled:opacity-50 transition-[background-color,transform,opacity] duration-200"
              data-testid="checkout-submit-button"
            >
              {loading ? "Routing to Secure Checkout…" : `Proceed — $${selected?.price.toLocaleString()}/${selected?.interval === "month" ? "mo" : "yr"}`}
            </button>
            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-600 text-center">
              Secured by Stripe // Licence issued instantly after payment
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
};
