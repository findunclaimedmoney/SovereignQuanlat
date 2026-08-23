import { Nav } from "@/components/Nav";
import { Hero } from "@/components/Hero";
import { EditorialMarquee } from "@/components/EditorialMarquee";
import { Manifesto } from "@/components/Manifesto";
import { Pricing } from "@/components/Pricing";
import { Footer } from "@/components/Footer";
import { Concierge } from "@/components/Concierge";

export default function Landing() {
  return (
    <main data-testid="landing-page">
      <Nav />
      <Hero />
      <EditorialMarquee />
      <Manifesto />
      <Pricing />
      <Footer />
      <Concierge />
    </main>
  );
}
