"use client";

import { motion } from "motion/react";
import {
  Target,
  Shield,
  AlertTriangle,
  GitCommit,
  Settings,
  Zap,
  Search,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: Target,
    badge: "Auto-match",
    badgeVariant: "success" as const,
    title: "Calibrated 0.95 threshold",
    description:
      "Adversarial Challenge Referee corpus validates zero false positives. Threshold maximizes throughput while keeping recall tight on noisy real-world gaps.",
  },
  {
    icon: Shield,
    badge: "Conservation",
    badgeVariant: "info" as const,
    title: "Strict In = Out guarantee",
    description:
      "Input record count equals output record count — mathematically enforced. No record is ever dropped, duplicated, or silently transformed.",
  },
  {
    icon: AlertTriangle,
    badge: "Review queue",
    badgeVariant: "warning" as const,
    title: "Three severity lanes",
    description:
      "Ambiguous (multiple candidates), Weak Evidence (below threshold), Leftover (no counterpart). Each packet carries actionable semantic findings.",
  },
  {
    icon: Search,
    badge: "Explainability",
    badgeVariant: "info" as const,
    title: "Missing vs contradictory",
    description:
      "Semantic findings classify disagreement: missing evidence (nothing contradicts) vs contradictory evidence (signals disagree). Root-cause trace included.",
  },
  {
    icon: GitCommit,
    badge: "Provenance",
    badgeVariant: "info" as const,
    title: "Engine version + config hash",
    description:
      "Every result carries the engine version and configuration hash. Reproducible across runs, auditable across teams.",
  },
  {
    icon: Settings,
    badge: "Configurable",
    badgeVariant: "neutral" as const,
    title: "Deterministic parameters",
    description:
      "No ML randomness. Weights, thresholds, and temporal windows are explicit config. Change them and the output changes predictably.",
  },
];

export function Features() {
  return (
    <section id="features" className="py-14 sm:py-20 lg:py-24" aria-labelledby="features-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-4xl text-center"
      >
        <Badge variant="info" className="mb-4 inline-flex">
          <Zap className="size-3 mr-1.5" aria-hidden="true" />
          Built for auditors, not demos
        </Badge>
        <h2 id="features-heading" className="text-3xl sm:text-4xl font-medium tracking-[-0.02em]">
          Features that matter for compliance
        </h2>
        <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Every feature serves the core promise: prove the match, explain the exception, lose nothing.
        </p>
      </motion.div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature, i) => (
          <motion.article
            key={feature.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.08 + i * 0.06 }}
          >
            <Card className="h-full hover:ring-2 hover:ring-primary/20 transition-all">
              <CardContent className="flex flex-col h-full p-6">
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="p-3 rounded-lg bg-primary/15 text-primary">
                    <feature.icon className="size-6" aria-hidden="true" />
                  </div>
                  <Badge variant={feature.badgeVariant}>{feature.badge}</Badge>
                </div>
                <h3 className="text-lg font-semibold mb-2 text-foreground">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed flex-1">{feature.description}</p>
              </CardContent>
            </Card>
          </motion.article>
        ))}
      </div>
    </section>
  );
}