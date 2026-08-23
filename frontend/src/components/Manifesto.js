import { motion } from "framer-motion";

const EASE = [0.76, 0, 0.24, 1];

const CHAPTERS = [
  {
    number: "01",
    title: "Orchestrate",
    body: "The Orchestrator routes natural-language objectives to specialized in-process agents — Data, Strategy, Risk, Reporting, Licence. Every message is correlation-traced. No cloud. No telemetry. No witness.",
    bullets: ["Natural-language goal routing", "Correlation-traced agent logs", "Five specialized offline agents"],
    image:
      "https://images.pexels.com/photos/38412413/pexels-photo-38412413.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    alt: "Monitors displaying market charts in a dim room",
    flip: false,
  },
  {
    number: "02",
    title: "Strategize",
    body: "Validate edge from first principles. Pairs statistical arbitrage with Engle-Granger cointegration, volatility-sized momentum with ADX gating, and regime-filtered mean reversion — tuned live in the playground.",
    bullets: ["Pairs stat-arb Z-score engine", "Momentum with ADX trend filter", "Regime-gated mean reversion"],
    image:
      "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjB0cmFkaW5nJTIwZGVzayUyMGRhcmt8ZW58MHx8fHwxNzg3NDUyNzQ1fDA&ixlib=rb-4.1.0&q=85",
    alt: "Candlestick chart on a dark screen",
    flip: true,
  },
  {
    number: "03",
    title: "Fortify",
    body: "RiskManager is a non-bypassable runtime gate. Every order clears daily-loss, drawdown, leverage and portfolio-heat checks — or it does not exist. Breach the drawdown limit and the kill switch locks the machine.",
    bullets: ["Non-bypassable order gates", "Kill-switch circuit breaker", "Offline HMAC licence activation"],
    image:
      "https://images.pexels.com/photos/37730212/pexels-photo-37730212.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
    alt: "Close-up of server racks",
    flip: false,
  },
];

const Chapter = ({ chapter, index }) => (
  <motion.article
    initial={{ opacity: 0, y: 60 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-120px" }}
    transition={{ duration: 1, ease: EASE }}
    className={`grid grid-cols-1 lg:grid-cols-12 gap-12 items-center ${
      chapter.flip ? "" : ""
    }`}
    data-testid={`manifesto-chapter-${chapter.number}`}
  >
    <div className={`lg:col-span-6 ${chapter.flip ? "lg:order-2" : ""}`}>
      <div className="relative overflow-hidden border border-white/10">
        <motion.img
          src={chapter.image}
          alt={chapter.alt}
          loading="lazy"
          initial={{ scale: 1.15 }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 1.6, ease: EASE }}
          className="w-full h-[320px] md:h-[440px] object-cover grayscale contrast-125 hover:grayscale-0 transition-[filter] duration-700"
          data-testid={`manifesto-image-${chapter.number}`}
        />
        <span className="absolute top-4 left-4 bg-black/60 backdrop-blur-xl border border-white/10 px-3 py-1 text-[10px] uppercase tracking-[0.25em] text-zinc-400">
          FIG. {chapter.number}
        </span>
      </div>
    </div>

    <div className={`lg:col-span-6 ${chapter.flip ? "lg:order-1" : ""}`}>
      <span
        className="font-display text-7xl md:text-8xl font-black text-outline block leading-none"
        data-testid={`manifesto-number-${chapter.number}`}
      >
        {chapter.number}
      </span>
      <h3 className="font-display text-4xl md:text-5xl font-black uppercase tracking-tight mt-4">
        {chapter.title}
      </h3>
      <p className="mt-6 text-base md:text-lg leading-relaxed text-zinc-400 max-w-lg">
        {chapter.body}
      </p>
      <ul className="mt-8 space-y-3">
        {chapter.bullets.map((b, i) => (
          <li
            key={i}
            className="flex items-center gap-4 text-xs uppercase tracking-[0.2em] text-zinc-500"
          >
            <span className="h-px w-8 bg-[#3B82F6]" />
            {b}
          </li>
        ))}
      </ul>
    </div>
  </motion.article>
);

export const Manifesto = () => (
  <section id="manifesto" className="px-6 md:px-12 py-32 md:py-48" data-testid="manifesto-section">
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.9, ease: EASE }}
      className="mb-24 md:mb-32"
    >
      <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
        The Manifesto
      </p>
      <h2 className="font-display text-4xl md:text-5xl lg:text-6xl leading-none tracking-tight uppercase font-black max-w-4xl">
        Your machine. Your models. <span className="text-outline">Your edge.</span>
      </h2>
    </motion.div>

    <div className="space-y-32 md:space-y-48">
      {CHAPTERS.map((c, i) => (
        <Chapter key={c.number} chapter={c} index={i} />
      ))}
    </div>
  </section>
);
