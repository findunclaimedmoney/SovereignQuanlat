import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { CornerDownLeft } from "lucide-react";
import { Link } from "react-router-dom";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const GREETING = {
  role: "assistant",
  content:
    "ATLAS online. I coach the Sovereign Quant workstation — strategy mechanics, risk discipline, operations. Software education only. State your question.",
};

export const CoachChat = () => {
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([GREETING]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    axios
      .get(`${API}/coach/status`, { withCredentials: true })
      .then((r) => setActive(r.data.active))
      .catch(() => setActive(false));
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || streaming) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setStreaming(true);
    try {
      const res = await fetch(`${API}/coach/chat`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error("coach request failed");
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

  if (active === null) return null;

  if (!active) {
    return (
      <div className="border border-white/10 bg-[#0A0A0A] p-6" data-testid="coach-upsell">
        <p className="text-sm text-zinc-400 leading-relaxed">
          AI Coach is not active on this account.{" "}
          <Link to="/#pricing" className="text-[#FF3333]">Add it for $49/mo</Link>{" "}
          — Claude-Opus mentorship on strategies, risk gates and workstation
          operations. Software education, never investment advice.
        </p>
      </div>
    );
  }

  return (
    <div className="border border-[#FF3333]/40 bg-[#0A0A0A]" data-testid="coach-chat-panel">
      <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
        <p className="text-[10px] uppercase tracking-[0.25em] text-zinc-500">Atlas // AI Coach</p>
        <span className="flex items-center gap-2 text-[10px] uppercase tracking-[0.2em] text-[#00FF66]">
          <span className="h-1.5 w-1.5 rounded-full bg-[#00FF66] animate-pulse" />
          Active
        </span>
      </div>
      <div ref={scrollRef} className="h-80 overflow-y-auto px-5 py-4 space-y-4" data-testid="coach-messages">
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
          placeholder="Ask your coach…"
          className="flex-1 bg-transparent px-3 py-2 text-xs outline-none placeholder:text-zinc-600"
          data-testid="coach-input"
        />
        <button
          onClick={send}
          disabled={streaming}
          className="flex h-9 w-9 items-center justify-center bg-[#FF3333] text-white hover:bg-red-700 active:scale-95 disabled:opacity-40 transition-[background-color,transform,opacity] duration-200"
          aria-label="Send coach message"
          data-testid="coach-send-button"
        >
          <CornerDownLeft className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};
