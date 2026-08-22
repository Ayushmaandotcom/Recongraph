"use client";

import { motion, useReducedMotion } from "motion/react";
import { useLayoutEffect } from "react";
import { Nav } from "./nav";
import { Hero } from "./hero";
import { Problem } from "./problem";
import { HowItWorks } from "./how-it-works";
import { Features } from "./features";
import { Trust } from "./trust";
import { Faq } from "./faq";
import { FinalCta } from "./final-cta";
import { Footer } from "./footer";
import { SectionDivider } from "./section-divider";

const CONTENT_WIDTH =
  "mx-auto max-w-[76rem] w-[calc(100%-1rem)] sm:w-[calc(100%-2rem)] md:w-[calc(100%-3rem)] lg:w-[calc(100%-4rem)] xl:w-full";

export function LandingPage() {
  const shouldReduceMotion = useReducedMotion();

  useLayoutEffect(() => {
    if ("scrollRestoration" in history) {
      history.scrollRestoration = "manual";
    }
    window.scrollTo(0, 0);
  }, []);

  return (
    <main
      className="relative isolate min-h-svh bg-background text-foreground"
      style={{
        "--rail": "color-mix(in oklch, var(--foreground) 12%, transparent)",
      } as React.CSSProperties}
    >
      <div className="pointer-events-none fixed inset-0 z-0">
        <div
          className="h-full w-full bg-[radial-gradient(ellipse_at_50%_0%,var(--color-primary)/0.06,transparent_60%)]"
          aria-hidden="true"
        />
      </div>

      <motion.div
        className="overflow-hidden"
        initial={
          shouldReduceMotion ? false : { opacity: 0.6, filter: "blur(16px)" }
        }
        animate={{ opacity: 1, filter: "blur(0px)" }}
        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
      >
        <div className={`relative ${CONTENT_WIDTH}`}>
          <Nav />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <Hero />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <Problem />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <HowItWorks />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <Features />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <Trust />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <Faq />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH}`}>
          <FinalCta />
        </div>

        <SectionDivider />

        <div className={`relative ${CONTENT_WIDTH} pb-16`}>
          <Footer />
        </div>
      </motion.div>
    </main>
  );
}