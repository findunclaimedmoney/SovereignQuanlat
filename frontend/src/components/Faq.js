import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Plus, Minus } from "lucide-react";

const EASE = [0.76, 0, 0.24, 1];

const FAQS = [
  {
    q: "Is this legal?",
    a: "Yes. You are buying analytical software that runs on your own computer — like buying a spreadsheet or a charting tool. You alone are responsible for your trading decisions and for following the rules in your jurisdiction.",
  },
  {
    q: "Does it place real trades?",
    a: "No. Sovereign Quant researches and simulates strategies and enforces risk limits on its own paper engine. It never connects to a broker, never holds your money, and never sends an order anywhere. What you do with the research is entirely yours.",
  },
  {
    q: "What do I need to run it?",
    a: "Any Windows, Mac or Linux computer with Python 3.10 or newer. No broker account, no API keys, no subscriptions to data feeds — and after installation, no internet connection either.",
  },
  {
    q: "Is there a refund policy?",
    a: "If the workstation fails to install or activate on your machine, the desk refunds you — full stop. For anything else, ask the concierge before you buy; it answers honestly, including when the answer is that this product is not for you.",
  },
  {
    q: "What happens if I lose money?",
    a: "Sovereign Quant makes no promise of returns and gives no investment advice. Markets carry real risk of loss. The software exists to help you research and enforce discipline — never trade money you cannot afford to lose.",
  },
  {
    q: "Where does my data go?",
    a: "Nowhere. The workstation runs fully offline with zero telemetry. Licence activation is local cryptography (HMAC) — our servers never see your machine, your strategies, or your results.",
  },
];

export const Faq = () => {
  const [open, setOpen] = useState(1);

  return (
    <section id="faq" className="px-6 md:px-12 py-32 border-t border-white/10" data-testid="faq-section">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mb-16"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-6">
          Objections, Answered
        </p>
        <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black">
          Asked <span className="text-outline">first.</span>
        </h2>
      </motion.div>

      <div className="max-w-4xl">
        {FAQS.map((item, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ duration: 0.7, delay: i * 0.06, ease: EASE }}
            className="border-b border-white/10"
            data-testid={`faq-item-${i}`}
          >
            <button
              onClick={() => setOpen(open === i ? -1 : i)}
              className="w-full flex items-center justify-between py-6 text-left group"
              data-testid={`faq-toggle-${i}`}
            >
              <span className="text-base md:text-lg font-medium text-[#F5F5F0] group-hover:text-[#FF3333] transition-colors duration-200">
                {item.q}
              </span>
              {open === i ? (
                <Minus className="h-4 w-4 text-[#FF3333] shrink-0" />
              ) : (
                <Plus className="h-4 w-4 text-zinc-500 shrink-0" />
              )}
            </button>
            <AnimatePresence>
              {open === i && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.4, ease: EASE }}
                  className="overflow-hidden"
                >
                  <p className="pb-6 text-sm md:text-base leading-relaxed text-zinc-400 max-w-2xl" data-testid={`faq-answer-${i}`}>
                    {item.a}
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </section>
  );
};
