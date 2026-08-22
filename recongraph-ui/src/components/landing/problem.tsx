"use client";

import { motion } from "motion/react";
import { FileText, AlertTriangle, Shuffle, Zap } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const problems = [
  {
    icon: FileText,
    title: "Evidence fragmentation",
    description:
      "A single purchase generates a vendor invoice, PR entry, GST record, and bank transaction — each with different vendor names, reference formats, and dates. Spreadsheets can't connect them reliably.",
  },
  {
    icon: AlertTriangle,
    title: "Silent mismatches",
    description:
      "Amount rounding (±₹1), minor date drifts, and GSTIN variations produce false mismatches. Teams waste hours investigating noise instead of real exceptions.",
  },
  {
    icon: Shuffle,
    title: "Unexplainable matches",
    description:
      "Traditional fuzzy matching gives a score but no rationale. When auditors ask \"why did this match?\", there's no evidence trail — only a black-box percentage.",
  },
  {
    icon: Zap,
    title: "No conservation guarantee",
    description:
      "Record counts drift during reconciliation. Input records ≠ output records. Data loss goes unnoticed until the audit.",
  },
];

export function Problem() {
  return (
    <section id="problem" className="py-14 sm:py-20 lg:py-24" aria-labelledby="problem-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-4xl text-center"
      >
        <h2 id="problem-heading" className="text-3xl sm:text-4xl font-medium tracking-[-0.02em]">
          Why reconciliation fails
        </h2>
        <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          GST reconciliation isn&apos;t a matching problem &mdash; it&apos;s an evidence problem. Four records describe
          one financial event, but they disagree on identity, reference, and timing.
        </p>
      </motion.div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {problems.map((problem, i) => (
          <motion.article
            key={problem.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.1 + i * 0.08 }}
          >
            <Card className="h-full hover:ring-2 hover:ring-primary/20 transition-all">
              <CardContent className="flex flex-col h-full p-6">
                <div className="mb-4 p-3 rounded-lg bg-primary/15 text-primary">
                  <problem.icon className="size-6" aria-hidden="true" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-foreground">{problem.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed flex-1">{problem.description}</p>
              </CardContent>
            </Card>
          </motion.article>
        ))}
      </div>
    </section>
  );
}