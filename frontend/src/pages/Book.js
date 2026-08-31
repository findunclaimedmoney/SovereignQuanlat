import { Link } from "react-router-dom";
import { motion } from "framer-motion";

const EASE = [0.76, 0, 0.24, 1];

const VOLUMES = [
  {
    id: "i",
    volume: "Volume I",
    title: "Sovereignty",
    edition: "Black & Gold",
    blurb:
      "The claim on the door. Desk versus dealer. Operator rights, vendor limits, and the non-bypassable gate.",
    cover: "/book/Sovereign_Quant_Volume_I_cover.jpg",
    pdf: "/book/Sovereign_Quant_Volume_I_Black_and_Gold.pdf",
    pages: "25 pages",
  },
  {
    id: "ii",
    volume: "Volume II",
    title: "Architecture",
    edition: "Blueprint",
    blurb:
      "Two machines, the orchestrator as shipped, agent map, data path, risk sequence, kill-switch states.",
    cover: "/book/Sovereign_Quant_Volume_II_cover.jpg",
    pdf: "/book/Sovereign_Quant_Volume_II_Architecture.pdf",
    pages: "16 pages",
  },
];

export default function Book() {
  return (
    <main className="min-h-screen bg-[#0B0F14] px-6 md:px-12 py-24" data-testid="book-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mx-auto max-w-6xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          Manuscript
        </p>
        <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-black uppercase tracking-tight leading-none">
          The books of the <span className="text-outline">desk</span>.
        </h1>
        <p className="mt-6 max-w-xl text-base md:text-lg text-zinc-400">
          Volume I is doctrine. Volume II is the map of what ships. Software
          licensing only — not investment advice. Also listed on Google Play
          Books when those listings go live.
        </p>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8">
          {VOLUMES.map((v) => (
            <article
              key={v.id}
              className="border border-white/10 bg-[#111827] p-6 md:p-8"
              data-testid={`book-card-${v.id}`}
            >
              <img
                src={v.cover}
                alt={`${v.volume} ${v.title} cover`}
                className="w-full aspect-[2/3] object-cover border border-white/10 bg-black"
              />
              <p className="mt-6 text-[10px] uppercase tracking-[0.25em] text-[#F59E0B]">
                {v.edition} · {v.pages}
              </p>
              <h2 className="mt-2 font-display text-2xl md:text-3xl font-black uppercase tracking-tight">
                {v.volume}
                <span className="block text-zinc-400 text-lg mt-1">{v.title}</span>
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-zinc-400">{v.blurb}</p>
              <a
                href={v.pdf}
                className="mt-8 inline-block bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
                data-testid={`book-download-${v.id}`}
              >
                Download PDF
              </a>
            </article>
          ))}
        </div>

        <p className="mt-12 text-xs text-zinc-500 max-w-xl">
          If a cover image is missing, the PDF link still works once the files
          sit in frontend/public/book/. Volume III is not published yet.
        </p>

        <div className="mt-10 flex gap-4 flex-wrap">
          <Link
            to="/guide"
            className="border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5"
          >
            Field manual
          </Link>
          <Link
            to="/"
            className="border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5"
          >
            Return to site
          </Link>
        </div>
      </motion.div>
    </main>
  );
}

