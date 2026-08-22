"use client";

import Image from "next/image";
import { motion } from "motion/react";
import { ArrowRight, CheckCircle, Shield, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Hero() {
  const trustItems = [
    { icon: CheckCircle, label: "0 FP on adversarial corpus", color: "success" },
    { icon: Shield, label: "Strict conservation (In = Out)", color: "primary" },
    { icon: Zap, label: "Threshold calibrated at 0.95", color: "warning" },
  ];

  return (
    <section className="py-14 sm:py-20 lg:py-24" aria-labelledby="hero-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto flex max-w-5xl flex-col items-center gap-8 text-center"
      >
        <motion.h1
          id="hero-heading"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.1 }}
          className="text-[clamp(1.75rem,1rem+4vw,2.5rem)] sm:text-[clamp(2.25rem,1.25rem+4vw,3rem)] lg:text-[clamp(2.75rem,1.5rem+4.5vw,3.5rem)] leading-[1.05] font-medium tracking-[-0.03em] text-balance"
        >
          Prove every GST match.<br />
          <span className="text-primary">Explain every exception.</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
          className="max-w-2xl text-base sm:text-lg text-muted-foreground leading-relaxed"
        >
          Deterministic graph engine for Purchase Register vs GSTR-2B reconciliation.
          Auto-match with calibrated confidence, strict conservation guarantees, and an
          explainable human review queue.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <Button size="lg" asChild className="w-full sm:w-auto">
            <a href="/app?demo=1">
              Try the Challenge Demo
              <ArrowRight className="size-4 ml-2" aria-hidden="true" />
            </a>
          </Button>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
          className="relative w-full max-w-4xl"
        >
          <div className="relative aspect-video rounded-xl overflow-hidden border border-border bg-muted ring-1 ring-foreground/5">
            <Image
              src="/images/hero-dashboard.jpg"
              alt="ReconGraph dashboard showing reconciliation results with auto-match rates and review queue"
              fill
              className="object-cover opacity-90"
              priority
              sizes="(max-width: 768px) 100vw, (max-width: 1024px) 90vw, 80vw"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent pointer-events-none" />
            <div className="absolute bottom-4 left-4 right-4 flex flex-wrap items-center justify-center gap-3 pointer-events-auto">
              {trustItems.map((item, i) => (
                <motion.span
                  key={item.label}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: 0.5 + i * 0.1 }}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-background/80 backdrop-blur-sm border border-border text-xs font-medium"
                >
                  <item.icon
                    className={`size-3.5 text-[var(--color-${item.color})]`}
                    aria-hidden="true"
                  />
                  <span className="text-foreground">{item.label}</span>
                </motion.span>
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </section>
  );
}