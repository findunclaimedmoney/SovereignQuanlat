import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, X, CornerDownLeft, Trash2, Brain } from "lucide-react";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MODES = [
  ["sales", "Sales"],
  ["support", "Support"],
  ["quant", "Quant Desk"],
];

const getSessionId = () => {
  let id = localStorage.getItem("sq_concierge_session");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("sq_concierge_session", id);
  }
  return id;
};

const GREETING = {
  role: "assistant",
  content:
    "AXIOM online. I advise on Sovereign Quant licensing, tiers and deployment — and I remember what matters between visits. State your query.",
};

export const Concierge = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [mode, setMode] = useState("sales");
  const [memories, setMemories] = useState([]);
  const [showMemories, setShowMemories] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

  const refreshMemory = async () => {
    try {
      const { data } = await axios.get(`${API}/chat/memory/${getSessionId()}`);
      setMemories(data.facts || []);
    } catch {
      /* non-fatal */
    }
  };

  useEffect(() => {
    if (!open) return undefined;
    refreshMemory();
    axios
      .get(`${API}/chat/history/${getSessionId()}`)
      .then(({ data }) => {
        if (data.messages.length > 0) setMessages([GREETING, ...data.messages]);
      })
      .catch(() => {});
    return undefined;
  }, [open]);

  const clearChat = async () => {
    try {
      await axios.post(`${API}/chat/clear`, { session_id: getSessionId() });
      setMessages([GREETING]);
      setMemories([]);
      toast.success("CONCIERGE MEMORY WIPED");
    } catch {
      toast.error("CLEAR FAILED");
    }
  };

  const send = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: getSessionId(), message: text, mode }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const part of parts) {
          if (!part.startsWith("data: ")) continue;
          const data = part.slice(6);
          if (data === "[DONE]") break;
          try {
            const { delta } = JSON.parse(data);
            if (delta) {
              setMessages((m) => {
                const copy = [...m];
                copy[copy.length - 1] = {
                  role: "assistant",
                  content: copy[copy.length - 1].content + delta,
                };
                return copy;
              });
            }
          } catch {
            /* partial json chunk */
          }
        }
      }
      refreshMemory();
    } catch {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "assistant", content: "CONNECTION FAULT — please retransmit." };
        return copy;
      });
    }
    setStreaming(false);
  };

  return (
    <>
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 2.2, type: "spring", stiffness: 200, damping: 18 }}
        onClick={() => setOpen((o) => !o)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center border border-white/15 bg-black/60 backdrop-blur-2xl hover:border-[#F59E0B]/60 active:scale-95 transition-[border-color,transform] duration-200"
        aria-label="Open AI concierge"
        data-testid="concierge-toggle-button"
      >
        {open ? <X className="h-5 w-5" /> : <Bot className="h-5 w-5 text-[#F59E0B]" />}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.97 }}
            transition={{ duration: 0.35, ease: [0.76, 0, 0.24, 1] }}
            className="fixed bottom-24 right-6 z-50 flex h-[520px] w-[calc(100vw-3rem)] max-w-sm flex-col border border-white/10 bg-black/70 backdrop-blur-2xl"
            data-testid="concierge-panel"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.25em]">Axiom // Concierge</p>
                <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mt-1">
                  Claude // Persistent Memory
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowMemories((s) => !s)}
                  className={`flex items-center gap-1 text-[10px] uppercase tracking-[0.15em] transition-colors duration-200 ${
                    memories.length ? "text-[#10B981]" : "text-zinc-600"
                  }`}
                  aria-label="View remembered facts"
                  data-testid="concierge-memory-button"
                >
                  <Brain className="h-3.5 w-3.5" /> {memories.length}
                </button>
                <button
                  onClick={clearChat}
                  className="text-zinc-600 hover:text-[#F59E0B] transition-colors duration-200"
                  aria-label="Clear chat and memory"
                  data-testid="concierge-clear-button"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="flex border-b border-white/10" data-testid="concierge-mode-toggle">
              {MODES.map(([id, label]) => (
                <button
                  key={id}
                  onClick={() => setMode(id)}
                  className={`flex-1 py-2 text-[10px] font-bold uppercase tracking-[0.2em] transition-colors duration-200 ${
                    mode === id ? "bg-white text-black" : "text-zinc-500 hover:text-white"
                  }`}
                  data-testid={`concierge-mode-${id}-button`}
                >
                  {label}
                </button>
              ))}
            </div>

            {showMemories && (
              <div className="border-b border-white/10 px-5 py-3 max-h-28 overflow-y-auto" data-testid="concierge-memory-panel">
                {memories.length === 0 ? (
                  <p className="text-[10px] text-zinc-600 uppercase tracking-[0.15em]">Nothing remembered yet.</p>
                ) : (
                  memories.map((f, i) => (
                    <p key={i} className="text-[10px] text-zinc-400 leading-relaxed">— {f}</p>
                  ))
                )}
              </div>
            )}

            <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-4 space-y-4" data-testid="concierge-messages">
              {messages.map((m, i) => (
                <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
                  <span
                    className={`inline-block max-w-[85%] px-3 py-2 text-xs leading-relaxed ${
                      m.role === "user"
                        ? "bg-white text-black"
                        : "border border-white/10 bg-white/5 text-zinc-300"
                    }`}
                  >
                    {m.content || (streaming && i === messages.length - 1 ? "…" : "")}
                  </span>
                </div>
              ))}
            </div>

            <div className="border-t border-white/10 p-3 flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Query the concierge…"
                className="flex-1 bg-transparent px-3 py-2 text-xs outline-none placeholder:text-zinc-600"
                data-testid="concierge-input"
              />
              <button
                onClick={send}
                disabled={streaming}
                className="flex h-9 w-9 items-center justify-center bg-[#3B82F6] text-white hover:bg-blue-600 active:scale-95 disabled:opacity-40 transition-[background-color,transform,opacity] duration-200"
                aria-label="Send message"
                data-testid="concierge-send-button"
              >
                <CornerDownLeft className="h-4 w-4" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
