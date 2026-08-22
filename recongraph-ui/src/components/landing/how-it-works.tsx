"use client";

import { motion } from "motion/react";
import { Upload, GitBranch, CheckCircle, Search, FileText } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const steps = [
  {
    number: "01",
    icon: Upload,
    title: "Upload evidence",
    description:
      "Drop in Purchase Register CSV and GSTR-2B JSON. The engine normalizes vendor names, references, amounts, dates, and GSTINs deterministically.",
    detail: "No column mapping wizard. Schema is fixed by design.",
  },
  {
    number: "02",
    icon: GitBranch,
    title: "Graph matching",
    description:
      "Every record becomes a node. Edges are candidate relationships scored on entity, reference, amount, temporal, and tax-identity compatibility.",
    detail: "Scores are additive with explainable signal breakdown.",
  },
  {
    number: "03",
    icon: CheckCircle,
    title: "Auto-match or review",
    description:
      "Pairs above the calibrated 0.95 threshold auto-match. Everything else routes to the review queue with severity tags: Ambiguous, Weak Evidence, Leftover.",
    detail: "Zero false positives on Challenge Referee corpus.",
  },
  {
    number: "04",
    icon: Search,
    title: "Investigate packets",
    description:
      "Each review packet shows side-by-side evidence, semantic findings (missing vs contradictory), and the full explanation trajectory — why the engine couldn't decide.",
    detail: "One-click provenance trace to engine config hash.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-14 sm:py-20 lg:py-24" aria-labelledby="how-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-4xl text-center"
      >
        <Badge variant="info" className="mb-4 inline-flex">
          <GitBranch className="size-3 mr-1.5" aria-hidden="true" />
          4 steps from evidence to explanation
        </Badge>
        <h2 id="how-heading" className="text-3xl sm:text-4xl font-medium tracking-[-0.02em]">
          How it works
        </h2>
        <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Upload → Graph → Decide → Investigate. Every step is deterministic and auditable.
        </p>
      </motion.div>

      <div className="mt-12 grid gap-6 lg:grid-cols-4">
        {steps.map((step, i) => (
          <motion.article
            key={step.number}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.1 + i * 0.1 }}
            className="relative"
          >
            <Card className="h-full">
              <CardContent className="flex flex-col h-full p-6">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl font-mono font-medium text-primary/30">{step.number}</span>
                  <div className="p-2 rounded-lg bg-primary/15 text-primary">
                    <step.icon className="size-5" aria-hidden="true" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2 text-foreground">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed mb-4 flex-1">{step.description}</p>
                <Badge variant="neutral" className="w-fit text-xs">
                  <FileText className="size-3 mr-1" aria-hidden="true" />
                  {step.detail}
                </Badge>
              </CardContent>
            </Card>
            {i < steps.length - 1 && (
              <motion.div
                className="hidden lg:block absolute top-10 left-full w-full h-0.5 bg-gradient-to-r from-primary/20 to-transparent"
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: 0.4 + i * 0.1 }}
                style={{ transformOrigin: "left center" }}
              />
            )}
          </motion.article>
        ))}
      </div>

      <motion.p
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="mt-10 text-center text-sm text-muted-foreground"
      >
        Conservative by default. Every match is provable. Every exception is explainable.
      </motion.p>
    </section>
  );
}