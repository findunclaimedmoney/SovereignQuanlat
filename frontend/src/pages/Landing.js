import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { EditorialMarquee } from "@/components/EditorialMarquee";
import { Manifesto } from "@/components/Manifesto";
import { PlainTalk } from "@/components/PlainTalk";
import { Proof } from "@/components/Proof";
import { Armory } from "@/components/Armory";
import { Pricing } from "@/components/Pricing";
import { Faq } from "@/components/Faq";
import { Footer } from "@/components/Footer";
import { Concierge } from "@/components/Concierge";
import { useEffect } from "react";
import { useSearchParams } from "react-router-dom";

export default function Landing() {
  const [params] = useSearchParams();

  useEffect(() => {
    const ref = params.get("ref");
    if (ref) localStorage.setItem("sq_ref", ref);
  }, [params]);

  return (
    <main data-testid="landing-page">
      <Nav />
      <Hero />
      <EditorialMarquee />
      <Manifesto />
      <PlainTalk />
      <Proof />
      <Armory />
      <Pricing />
      <Faq />
      <Footer />
      <Concierge />
    </main>
  );
}
