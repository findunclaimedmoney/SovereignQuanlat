import Marquee from "react-fast-marquee";

const ITEMS = [
  "Zero Cloud Telemetry",
  "Ed25519 Offline Licensing",
  "Non-Bypassable Risk Gates",
  "Multi-Agent Orchestration",
  "Kill-Switch Circuit Breaker",
  "$50M Max Capital — Institutional",
  "Branded Executive Tearsheets",
];

export const EditorialMarquee = () => (
  <div className="border-y border-white/10 py-5 overflow-hidden" data-testid="editorial-marquee">
    <Marquee speed={28} gradient={false} pauseOnHover>
      {ITEMS.map((item, i) => (
        <span
          key={i}
          className="mx-16 text-sm tracking-[0.2em] uppercase text-zinc-500 whitespace-nowrap"
        >
          {item} <span className="text-[#F59E0B] ml-16">/</span>
        </span>
      ))}
    </Marquee>
  </div>
);
