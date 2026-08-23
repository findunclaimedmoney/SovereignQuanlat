import { motion } from "framer-motion";

const EASE = [0.76, 0, 0.24, 1];

const BLOCKS = [
  {
    number: "01",
    title: "What it is",
    body: "A research workstation that runs entirely on your own computer. It tests trading strategies against market data, shows you the results, and refuses to let any strategy break the safety limits you set. Think flight simulator with a strict safety officer on board.",
  },
  {
    number: "02",
    title: "What it is not",
    body: "Not a broker. Not a fund. It never holds your money, never places trades for you, and never promises profits. If you later connect your own broker account, that account stays yours — at your own risk.",
  },
  {
    number: "03",
    title: "Who it is for",
    body: "Traders already comfortable with terms like drawdown and position sizing. New to all this? Start with the free Community tier, watch the six-step narrated guide, and add the AI Coach — it explains every feature in plain English.",
  },
];

export const PlainTalk = () => (
  <section id="plain-talk" className="px-6 md:px-12 py-32 border-t border-white/10" data-testid="plain-talk-section">
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.9, ease: EASE }}
      className="mb-16"
    >
      <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
        No Jargon
      </p>
      <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black">
        Plain <span className="text-outline">talk.</span>
      </h2>
    </motion.div>

    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {BLOCKS.map((block, i) => (
        <motion.div
          key={block.number}
          initial={{ opacity: 0, y: 60 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.9, delay: i * 0.12, ease: EASE }}
          className="border border-white/10 bg-[#151B24] p-8 md:p-10 hover:border-white/25 transition-colors duration-300"
          data-testid={`plain-talk-${block.number}`}
        >
          <span className="font-display text-5xl font-black text-outline leading-none">
            {block.number}
          </span>
          <h3 className="font-display text-2xl md:text-3xl font-light uppercase mt-6">
            {block.title}
          </h3>
          <p className="mt-5 text-base leading-relaxed text-zinc-400">{block.body}</p>
        </motion.div>
      ))}
    </div>

    <motion.p
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 1, delay: 0.4 }}
      className="mt-12 text-xs uppercase tracking-[0.2em] text-zinc-600 leading-relaxed max-w-3xl"
      data-testid="plain-talk-disclosure"
    >
      Sovereign Quant is analytical software, not financial advice. No strategy —
      ours or anyone's — comes with a track record we certify or a return we
      promise. You evaluate everything yourself, on your own machine, before a
      single dollar is ever at risk.
    </motion.p>
  </section>
);
