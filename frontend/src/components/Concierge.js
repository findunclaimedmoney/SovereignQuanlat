import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Bot, X, CornerDownLeft } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getSessionId = () => {
  let id = localStorage.getItem("sq_concierge_session");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("sq_concierge_session", id);
  }
  return id;
};

export const Concierge = () => {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "AXIOM online. I advise on Sovereign Quant licensing, tiers and deployment. State your query.",
    },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, open]);

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
        body: JSON.stringify({ session_id: getSessionId(), message: text }),
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
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center border border-white/15 bg-black/60 backdrop-blur-2xl hover:border-[#FF3333]/60 active:scale-95 transition-[border-color,transform] duration-200"
        aria-label="Open AI concierge"
        data-testid="concierge-toggle-button"
      >
        {open ? <X className="h-5 w-5" /> : <Bot className="h-5 w-5 text-[#FF3333]" />}
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.97 }}
            transition={{ duration: 0.35, ease: [0.76, 0, 0.24, 1] }}
            className="fixed bottom-24 right-6 z-50 flex h-[480px] w-[calc(100vw-3rem)] max-w-sm flex-col border border-white/10 bg-black/70 backdrop-blur-2xl"
            data-testid="concierge-panel"
          >
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.25em]">Axiom // Concierge</p>
                <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 mt-1">
                  Claude // Sovereign Quant
                </p>
              </div>
              <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-[#00FF66]">
                <span className="h-1.5 w-1.5 rounded-full bg-[#00FF66] animate-pulse" />
                Live
              </span>
            </div>

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
                className="flex h-9 w-9 items-center justify-center bg-[#FF3333] text-white hover:bg-red-700 active:scale-95 disabled:opacity-40 transition-[background-color,transform,opacity] duration-200"
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
