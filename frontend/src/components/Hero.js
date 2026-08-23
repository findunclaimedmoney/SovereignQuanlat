import { useMemo, useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { Canvas, useFrame } from "@react-three/fiber";

const EASE = [0.76, 0, 0.24, 1];

const MaskedLine = ({ children, delay }) => (
  <span className="block overflow-hidden">
    <motion.span
      className="block"
      initial={{ y: "110%" }}
      animate={{ y: "0%" }}
      transition={{ duration: 1.2, delay, ease: EASE }}
    >
      {children}
    </motion.span>
  </span>
);

function PointSphere() {
  const cloud = useRef();
  const cage = useRef();

  const positions = useMemo(() => {
    const count = 2600;
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const phi = Math.acos(2 * Math.random() - 1);
      const theta = Math.random() * Math.PI * 2;
      const r = 2.3 + (Math.random() - 0.5) * 0.12;
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      arr[i * 3 + 2] = r * Math.cos(phi);
    }
    return arr;
  }, []);

  useFrame((state, delta) => {
    if (cloud.current) {
      cloud.current.rotation.y += delta * 0.045;
      cloud.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.08) * 0.15;
    }
    if (cage.current) {
      cage.current.rotation.y -= delta * 0.02;
      cage.current.rotation.z += delta * 0.008;
    }
  });

  return (
    <group>
      <points ref={cloud}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" args={[positions, 3]} />
        </bufferGeometry>
        <pointsMaterial size={0.014} color="#8C8C94" sizeAttenuation transparent opacity={0.75} />
      </points>
      <mesh ref={cage}>
        <icosahedronGeometry args={[3.1, 1]} />
        <meshBasicMaterial color="#FF3333" wireframe transparent opacity={0.08} />
      </mesh>
    </group>
  );
}

export const Hero = () => {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [0, 220]);
  const opacity = useTransform(scrollYProgress, [0, 0.75], [1, 0]);

  return (
    <section
      ref={ref}
      id="top"
      className="relative h-screen overflow-hidden hero-grid-bg"
      data-testid="hero-section"
    >
      <div className="absolute inset-0 opacity-90">
        <Canvas camera={{ position: [0, 0, 6.2], fov: 50 }} dpr={[1, 1.5]}>
          <PointSphere />
        </Canvas>
      </div>
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,#050505_90%)]" />

      <motion.div
        style={{ y, opacity }}
        className="relative z-10 flex h-full flex-col justify-center px-6 md:px-12"
      >
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="text-xs uppercase tracking-[0.3em] text-[#FF3333] font-bold mb-8"
          data-testid="hero-overline"
        >
          Multi-Agent Quantitative Workstation — v1.3 Core
        </motion.p>

        <h1
          className="font-display text-5xl md:text-7xl lg:text-[8vw] leading-[0.85] tracking-tighter uppercase font-black"
          data-testid="hero-headline"
        >
          <MaskedLine delay={0.5}>Sovereign.</MaskedLine>
          <MaskedLine delay={0.65}>Quant.</MaskedLine>
          <MaskedLine delay={0.8}>
            <span className="text-outline">Offline.</span>
          </MaskedLine>
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.3, ease: EASE }}
          className="mt-10 max-w-xl text-base md:text-lg leading-relaxed text-zinc-400"
          data-testid="hero-subcopy"
        >
          Zero cloud telemetry. Non-bypassable risk gates. A cryptographically
          licensed trading engine that answers to no server but your own.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.5, ease: EASE }}
          className="mt-12 flex flex-wrap items-center gap-4"
        >
          <button
            onClick={() =>
              window.__lenis
                ? window.__lenis.scrollTo("#pricing", { offset: -72 })
                : document.querySelector("#pricing")?.scrollIntoView({ behavior: "smooth" })
            }
            className="bg-white text-black font-bold uppercase tracking-wider px-8 py-4 hover:bg-zinc-200 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="hero-acquire-button"
          >
            Acquire Licence
          </button>
          <button
            onClick={() =>
              window.__lenis
                ? window.__lenis.scrollTo("#manifesto", { offset: -72 })
                : document.querySelector("#manifesto")?.scrollIntoView({ behavior: "smooth" })
            }
            className="border border-white/20 text-white font-bold uppercase tracking-wider px-8 py-4 hover:bg-white/5 active:scale-95 transition-[background-color,transform] duration-200"
            data-testid="hero-manifesto-button"
          >
            Read the Manifesto
          </button>
        </motion.div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1.2, delay: 2 }}
        className="absolute bottom-0 left-0 right-0 z-10 flex items-center justify-between border-t border-white/10 px-6 md:px-12 py-4 text-[10px] md:text-xs uppercase tracking-[0.25em] text-zinc-500"
        data-testid="hero-status-bar"
      >
        <span>
          SYS <span className="text-[#00FF66]">ACTIVE</span>
        </span>
        <span className="hidden md:inline">HMAC-SHA256 // Offline Licensing</span>
        <span className="tabular">LAT 40.7128 — LON 74.0060</span>
      </motion.div>
    </section>
  );
};
