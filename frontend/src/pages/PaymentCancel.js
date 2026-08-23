import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function PaymentCancel() {
  return (
    <main className="min-h-screen bg-[#0B0F14] px-6 md:px-12 py-24 hero-grid-bg" data-testid="payment-cancel-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1] }}
        className="mx-auto max-w-3xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          Fulfilment Terminal
        </p>
        <h1 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight">
          Transaction <span className="text-outline">aborted.</span>
        </h1>
        <p className="mt-6 text-zinc-400 text-sm leading-relaxed max-w-xl">
          No charge was made and no licence was issued. The workstation remains
          in Community mode until you choose otherwise.
        </p>
        <Link
          to="/"
          className="mt-14 inline-block bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
          data-testid="cancel-return-home-link"
        >
          Return to Pricing
        </Link>
      </motion.div>
    </main>
  );
}
