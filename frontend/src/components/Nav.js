import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useAuth } from "@/context/AuthContext";

const scrollTo = (target) => {
  if (window.__lenis) {
    window.__lenis.scrollTo(target, { offset: -72 });
  } else {
    document.querySelector(target)?.scrollIntoView({ behavior: "smooth" });
  }
};

export const Nav = () => {
  const [scrolled, setScrolled] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -80 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.9, ease: [0.76, 0, 0.24, 1], delay: 0.2 }}
      className={`fixed top-0 left-0 right-0 z-50 border-b transition-colors duration-500 ${
        scrolled
          ? "border-white/10 bg-black/60 backdrop-blur-2xl"
          : "border-transparent bg-transparent"
      }`}
      data-testid="main-nav"
    >
      <div className="flex items-center justify-between px-6 md:px-12 h-[72px]">
        <button
          onClick={() => scrollTo("#top")}
          className="font-display text-sm md:text-base font-black tracking-tighter uppercase"
          data-testid="nav-logo"
        >
          Sovereign<span className="text-[#FF3333]">//</span>Quant
        </button>

        <nav className="hidden md:flex items-center gap-10 text-xs uppercase tracking-[0.2em] text-zinc-400">
          {[
            ["Manifesto", "#manifesto", "nav-manifesto-link"],
            ["Pricing", "#pricing", "nav-pricing-link"],
            ["Guide", "/guide", "nav-guide-link"],
          ].map(([label, href, id], i) => (
            href.startsWith("/") ? (
              <a
                key={id + i}
                href={href}
                className="relative group py-2 hover:text-[#F5F5F0] transition-colors duration-300"
                data-testid={id}
              >
                {label}
                <span className="absolute left-0 bottom-0 h-px w-0 bg-[#FF3333] transition-[width] duration-300 group-hover:w-full" />
              </a>
            ) : (
            <button
              key={id + i}
              onClick={() => scrollTo(href)}
              className="relative group py-2 hover:text-[#F5F5F0] transition-colors duration-300"
              data-testid={id}
            >
              {label}
              <span className="absolute left-0 bottom-0 h-px w-0 bg-[#FF3333] transition-[width] duration-300 group-hover:w-full" />
            </button>
            )
          ))}
        </nav>

        <div className="flex items-center gap-4">
          <a
            href={user ? "/dashboard" : "/login"}
            className="hidden md:inline-block text-xs uppercase tracking-[0.2em] text-zinc-400 hover:text-white transition-colors duration-300"
            data-testid="nav-account-link"
          >
            {user ? "Dashboard" : "Sign In"}
          </a>
          <button
            onClick={() => scrollTo("#pricing")}
            className="bg-white text-black text-xs font-bold uppercase tracking-wider px-5 py-3 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="nav-acquire-licence-button"
          >
            Acquire Licence
          </button>
        </div>
      </div>
    </motion.header>
  );
};
