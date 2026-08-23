export const Footer = () => (
  <footer id="deploy" className="border-t border-white/10 px-6 md:px-12 py-20" data-testid="site-footer">
    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
      <div>
        <p className="font-display text-lg font-black uppercase tracking-tighter">
          Sovereign<span className="text-[#F59E0B]">//</span>Quant
        </p>
        <p className="mt-4 text-sm leading-relaxed text-zinc-500 max-w-xs">
          Offline-first multi-agent quantitative workstation. Self-owned,
          self-hosted, cryptographically licensed.
        </p>
      </div>

      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">Deploy</p>
        <div className="border border-white/10 bg-[#111827] p-4 text-xs text-zinc-400 space-y-2">
          <p><span className="text-zinc-600">$</span> run.bat <span className="text-zinc-600">// windows</span></p>
          <p><span className="text-zinc-600">$</span> ./run.sh <span className="text-zinc-600">// mac / linux</span></p>
          <p><span className="text-zinc-600">→</span> localhost:8501</p>
        </div>
      </div>

      <div>
        <p className="text-xs uppercase tracking-[0.25em] text-zinc-500 mb-4">Compliance</p>
        <p className="text-xs leading-relaxed text-zinc-600 max-w-xs">
          Sovereign Quant is analytical software, not financial advice. Trading
          involves substantial risk of loss. Licences are annual, per-machine,
          and non-transferable. All sales processed by Stripe.
        </p>
      </div>
    </div>

    <div className="mt-16 pt-6 border-t border-white/10 flex flex-col md:flex-row justify-between gap-4 text-[10px] uppercase tracking-[0.25em] text-zinc-600">
      <span>© 2026 Sovereign Quant Systems</span>
      <span className="flex gap-8">
        <a href="/portal" className="hover:text-zinc-300 transition-colors duration-200" data-testid="footer-portal-link">Buyer Portal</a>
        <span>Zero telemetry // Zero cloud // Zero compromise</span>
      </span>
    </div>
  </footer>
);
