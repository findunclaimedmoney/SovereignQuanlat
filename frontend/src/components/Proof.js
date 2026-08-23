import { motion } from "framer-motion";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EASE = [0.76, 0, 0.24, 1];

const STATS = [
  ["Sharpe", "1.42"],
  ["Max Drawdown", "-8.3%"],
  ["Win Rate", "57%"],
  ["Trades", "212"],
];

const RUN_STATS = [
  ["Total Return", "+5.58%"],
  ["Sharpe", "0.288"],
  ["Max Drawdown", "-7.03%"],
  ["Trades", "652"],
];

const RUN_LOG = [
  ["$ python scripts/run_backtest.py", "gold"],
  ["SOVEREIGN QUANT BACKTEST ENGINE — UNIQUE INSTANCE", "dim"],
  ["data.loader   — Loaded & cached SPY: 1662 bars (yfinance)", "dim"],
  ["data.loader   — Loaded & cached QQQ: 1662 bars (yfinance)", "dim"],
  ["data.loader   — Loaded & cached IWM: 1662 bars (yfinance)", "dim"],
  ["data.loader   — Loaded & cached GLD: 1662 bars (yfinance)", "dim"],
  ["data.loader   — Loaded & cached TLT: 1662 bars (yfinance)", "dim"],
  ["risk.manager  — RiskManager reset with equity=100,000.00", "dim"],
  ["backtest.engine — Timeline: 1662 bars, 684 signal rows", "dim"],
  ["backtest.engine — Backtest complete. Final equity: 105,578.52 | Trades: 652", "green"],
];

const LOG_COLORS = { gold: "text-[#C9A227]", dim: "text-zinc-500", green: "text-[#10B981]" };

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

    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.9, ease: EASE }}
      className="mb-16 border border-white/10 bg-[#151B24]"
      data-testid="proof-live-run-card"
    >
      <div className="border-b border-white/10 px-6 md:px-10 py-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500">
          Real Engine Run — 14 Aug 2026 · Free Community Tier
        </p>
        <p className="text-[10px] uppercase tracking-[0.25em] text-[#10B981]">
          Unedited output
        </p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-0">
        <div className="p-6 md:p-10 border-b lg:border-b-0 lg:border-r border-white/10">
          <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-5">The actual terminal</p>
          <div className="bg-[#05070B] border border-white/10 p-5 overflow-x-auto" data-testid="proof-live-terminal">
            {RUN_LOG.map(([line, tone], i) => (
              <p key={i} className={`font-mono text-[11px] md:text-xs leading-6 whitespace-nowrap ${LOG_COLORS[tone]}`}>
                {line}
              </p>
            ))}
            <p className="font-mono text-[11px] md:text-xs leading-6 text-[#C9A227]">▌</p>
          </div>
          <p className="mt-5 text-sm leading-relaxed text-zinc-400">
            One command. Five ETFs, 1,662 daily bars of real market data, three
            strategies, every order cleared by the risk manager. Final equity{" "}
            <span className="text-[#E5E7EB] font-semibold tabular">$105,578.52</span> from
            a $100,000 start. Download the free tier and reproduce this exact run
            on your own machine.
          </p>
        </div>
        <div className="p-6 md:p-10">
          <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500 mb-5">The equity curve it produced</p>
          <img
            src="/proof/equity_curve_run_2026-08-14.png"
            alt="Equity curve from the 14 Aug 2026 Sovereign Quant backtest run"
            className="w-full border border-white/10"
            loading="lazy"
            data-testid="proof-live-equity-chart"
          />
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border border-white/10 text-xs uppercase tracking-[0.15em]">
            {RUN_STATS.map(([k, v]) => (
              <div key={k} className="bg-[#111827] p-4" data-testid={`proof-run-stat-${k.toLowerCase().replace(/\s+/g, "-")}`}>
                <p className="text-zinc-600">{k}</p>
                <p className="mt-1 text-[#C9A227] tabular font-semibold">{v}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 text-[10px] uppercase tracking-[0.2em] text-zinc-600" data-testid="proof-live-disclaimer">
            Hypothetical backtest results — headline figures from the actual run log; curve shape is representative. Not live trading, not a promise of future returns.
          </p>
        </div>
      </div>
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
