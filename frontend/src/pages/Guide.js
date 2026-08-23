import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Play, Square } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const EASE = [0.76, 0, 0.24, 1];

const STEPS = [
  {
    id: "1",
    title: "Acquire Your Licence",
    body: "Choose Professional or Institutional on the pricing section, enter your licensee name, and complete checkout. Your HMAC key is signed and shown instantly on the confirmation page — and emailed to you as backup.",
  },
  {
    id: "2",
    title: "Download the Workstation",
    body: "From the same confirmation page, hit Download Workstation. You receive a zip containing the dashboard app, dependency list, and one-command launchers for Windows, Mac and Linux. Unpack it anywhere on your machine.",
  },
  {
    id: "3",
    title: "Install Dependencies",
    body: "Open a terminal inside the unpacked folder. You need Python 3.10 or newer. One command pulls in everything the workstation needs.",
    terminal: ["cd sovereign-quant-workstation", "pip install -r requirements.txt"],
  },
  {
    id: "4",
    title: "Launch the Engine",
    body: "Run the launcher for your platform. The workstation boots fully offline and opens in your browser at localhost:8501. Nothing leaves your machine.",
    terminal: ["run.bat        :: windows", "./run.sh       :: mac / linux", "# → http://localhost:8501"],
  },
  {
    id: "5",
    title: "Activate Offline",
    body: "In the sidebar, open Licence Management → Activate New Licence Key. Paste the key from your confirmation page. Verification is local HMAC — no internet call, no phone-home. Your tier unlocks instantly.",
  },
  {
    id: "6",
    title: "Operate",
    body: "Dispatch natural-language goals in the Orchestrator, tune strategies in the Playground, and watch every order pass through the non-bypassable risk gates. Breach your drawdown limit and the kill switch locks the machine. Branded tearsheets compile from the Reports tab.",
    image: "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA2MDV8MHwxfHNlYXJjaHwxfHxmaW5hbmNpYWwlMjB0cmFkaW5nJTIwZGVzayUyMGRhcmt8ZW58MHx8fHwxNzg3NDUyNzQ1fDA&ixlib=rb-4.1.0&q=85",
  },
];

const StepCard = ({ step, index, playingId, setPlayingId }) => {
  const audioRef = useRef(null);
  const playing = playingId === step.id;

  const toggle = () => {
    if (playing) {
      audioRef.current?.pause();
      setPlayingId(null);
      return;
    }
    setPlayingId(step.id);
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 60 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.9, ease: EASE }}
      className="grid grid-cols-1 lg:grid-cols-12 gap-8 border border-white/10 bg-[#111827] p-8 md:p-10"
      data-testid={`guide-step-${step.id}`}
    >
      <div className="lg:col-span-2">
        <span className="font-display text-6xl md:text-7xl font-black text-outline leading-none">
          {step.id}
        </span>
      </div>
      <div className="lg:col-span-7">
        <h3 className="font-display text-2xl md:text-3xl font-black uppercase tracking-tight">
          {step.title}
        </h3>
        <p className="mt-4 text-sm md:text-base leading-relaxed text-zinc-400">{step.body}</p>
        {step.terminal && (
          <div className="mt-6 border border-white/10 bg-black/60 p-4 text-xs md:text-sm text-zinc-300 space-y-1">
            {step.terminal.map((line, i) => (
              <p key={i}><span className="text-[#F59E0B]">$</span> {line}</p>
            ))}
          </div>
        )}
      </div>
      <div className="lg:col-span-3 flex flex-col justify-between gap-6">
        <button
          onClick={toggle}
          className={`flex items-center gap-3 border px-5 py-4 text-xs font-bold uppercase tracking-wider active:scale-95 transition-[background-color,border-color,transform] duration-200 ${
            playing
              ? "border-[#F59E0B] bg-[#F59E0B]/10 text-[#F59E0B]"
              : "border-white/20 text-white hover:bg-white/5"
          }`}
          data-testid={`guide-narration-button-${step.id}`}
        >
          {playing ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          {playing ? "Stop Narration" : "Play Narration"}
        </button>
        {step.image && (
          <img
            src={step.image}
            alt={step.title}
            loading="lazy"
            className="w-full h-36 object-cover grayscale contrast-125 border border-white/10"
          />
        )}
        {playing && (
          <audio
            ref={audioRef}
            src={`${API}/guide/narration/${step.id}`}
            autoPlay
            onEnded={() => setPlayingId(null)}
            data-testid={`guide-audio-${step.id}`}
          />
        )}
      </div>
    </motion.article>
  );
};

export default function Guide() {
  const [playingId, setPlayingId] = useState(null);

  return (
    <main className="min-h-screen bg-[#0B0F14] px-6 md:px-12 py-24" data-testid="guide-page">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease: EASE }}
        className="mx-auto max-w-5xl"
      >
        <p className="text-xs uppercase tracking-[0.3em] text-[#F59E0B] font-bold mb-6">
          Field Manual
        </p>
        <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-black uppercase tracking-tight leading-none">
          Zero to <span className="text-outline">sovereign</span> in six steps.
        </h1>
        <p className="mt-6 max-w-xl text-base md:text-lg text-zinc-400">
          Every step is narrated — press play on any chapter for the audio
          walkthrough, watch the full video below, or read at your own pace.
        </p>

        <div className="mt-12 border border-white/10 bg-[#111827]" data-testid="guide-video-section">
          <div className="border-b border-white/10 px-5 py-3 text-[10px] uppercase tracking-[0.25em] text-zinc-500 flex justify-between">
            <span>Full Walkthrough // Audio-Visual</span>
            <span className="text-[#10B981]">HD Voice</span>
          </div>
          <video
            controls
            preload="none"
            className="w-full aspect-video bg-black"
            src={`${API}/guide/video`}
            data-testid="guide-video-player"
          />
        </div>

        <div className="mt-16 space-y-8">
          {STEPS.map((s, i) => (
            <StepCard key={s.id} step={s} index={i} playingId={playingId} setPlayingId={setPlayingId} />
          ))}
        </div>

        <div className="mt-16 flex gap-4 flex-wrap">
          <Link
            to="/dashboard"
            className="bg-white text-black text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="guide-dashboard-link"
          >
            Go to Your Dashboard
          </Link>
          <Link
            to="/"
            className="border border-white/20 text-white text-xs font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="guide-home-link"
          >
            Return to Site
          </Link>
        </div>
      </motion.div>
    </main>
  );
}
