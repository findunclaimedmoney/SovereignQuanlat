import { motion } from "framer-motion";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EASE = [0.76, 0, 0.24, 1];

const STATS = [
  ["Sharpe", "1.42"],
  ["Max Drawdown", "-8.3%"],
  ["Win Rate", "57%"],
  ["Trades", "212"],
];

export const Proof = () => (
  <section id="proof" className="px-6 md:px-12 py-32 border-t border-white/10" data-testid="proof-section">
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.9, ease: EASE }}
      className="mb-16"
    >
      <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
        Receipts
      </p>
      <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black">
        See the output <span className="text-outline">before you pay.</span>
      </h2>
    </motion.div>

    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <motion.div
        initial={{ opacity: 0, y: 60 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.9, ease: EASE }}
        className="lg:col-span-7 border border-white/10 bg-[#151B24] p-8 md:p-10"
        data-testid="proof-tearsheet-card"
      >
        <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500">Sample Deliverable</p>
        <h3 className="font-display text-2xl md:text-3xl font-light uppercase mt-4">
          Executive Tearsheet
        </h3>
        <p className="mt-4 text-sm leading-relaxed text-zinc-400 max-w-lg">
          This is exactly what the workstation compiles — equity curve, drawdown
          profile, headline statistics. This sample runs on clearly-labeled
          synthetic data; your licence generates the same report on your own
          research, on your own machine.
        </p>
        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border border-white/10 text-xs uppercase tracking-[0.15em]">
          {STATS.map(([k, v]) => (
            <div key={k} className="bg-[#111827] p-4">
              <p className="text-zinc-600">{k}</p>
              <p className="mt-1 text-[#E5E7EB] tabular">{v}*</p>
            </div>
          ))}
        </div>
        <p className="mt-3 text-[10px] uppercase tracking-[0.2em] text-zinc-600">
          *Illustrative — synthetic data, not a track record
        </p>
        <a
          href={`${API}/sample-tearsheet`}
          className="mt-8 inline-block bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
          data-testid="download-sample-tearsheet-button"
        >
          Download Sample Tearsheet (PDF)
        </a>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 60 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.9, delay: 0.15, ease: EASE }}
        className="lg:col-span-5 border border-white/10 bg-[#151B24] p-8 md:p-10"
        data-testid="proof-who-card"
      >
        <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500">Behind the Desk</p>
        <h3 className="font-display text-2xl md:text-3xl font-light uppercase mt-4">
          One owner. <span className="text-[#F59E0B]">No investors.</span>
        </h3>
        <p className="mt-4 text-sm leading-relaxed text-zinc-400">
          Sovereign Quant is independently built and solely owned — no venture
          capital, no data resale, no ad networks. The business model is the
          price on the page and nothing else: licences, packs, and a coach
          subscription. The same person who wrote the risk gates answers the
          concierge.
        </p>
        <ul className="mt-8 space-y-3">
          {[
            "Sole ownership — the code answers to one desk",
            "Zero telemetry, verifiable offline",
            "No hidden fees, no trade commissions, ever",
          ].map((f, i) => (
            <li key={i} className="flex items-start gap-3 text-sm text-zinc-300">
              <span className="text-[#10B981] mt-0.5">+</span> {f}
            </li>
          ))}
        </ul>
      </motion.div>
    </div>
  </section>
);
