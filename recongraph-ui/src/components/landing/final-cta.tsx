"use client";

import { motion } from "motion/react";
import { ArrowRight, Zap, Shield, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

const highlights = [
  { icon: CheckCircle, label: "0 FP on adversarial corpus", color: "success" },
  { icon: Shield, label: "Strict conservation enforced", color: "primary" },
  { icon: Zap, label: "Deterministic & auditable", color: "warning" },
];

export function FinalCta() {
  return (
    <section className="py-14 sm:py-20 lg:py-24" aria-labelledby="cta-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-3xl text-center"
      >
        <h2 id="cta-heading" className="text-3xl sm:text-4xl lg:text-5xl font-medium tracking-[-0.02em] mb-4">
          Test the Engine
        </h2>

        <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
          Load the adversarial demo in seconds. See the review queue, inspect packets, trace the
          engine rationale. No signup, no data leaves your browser.
        </p>

        <Button size="lg" asChild className="w-full sm:w-auto mb-10">
          <a href="/app?demo=1">
            Load Demo Dataset
            <ArrowRight className="size-4 ml-2" aria-hidden="true" />
          </a>
        </Button>

        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
          {highlights.map((h) => (
            <span key={h.label} className="flex items-center gap-1.5 font-medium text-foreground">
              <h.icon className={`size-4 text-[var(--color-${h.color})]`} aria-hidden="true" />
              {h.label}
            </span>
          ))}
        </div>
      </motion.div>
    </section>
  );
}