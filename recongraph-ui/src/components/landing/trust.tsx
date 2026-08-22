"use client";

import { motion } from "motion/react";
import { CheckCircle, Shield, FileText, BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const stats = [
  { label: "False positives", value: "0", icon: CheckCircle, color: "success" },
  { label: "Conservation", value: "100%", icon: Shield, color: "primary" },
  { label: "Evidence types", value: "4", icon: FileText, color: "info" },
  { label: "Signal dimensions", value: "5", icon: BarChart3, color: "warning" },
];

const comparison = [
  { criterion: "Match rationale", spreadsheets: "Manual notes", recongraph: "Per-signal breakdown" },
  { criterion: "Conservation check", spreadsheets: "Manual count", recongraph: "Enforced by engine" },
  { criterion: "Threshold calibration", spreadsheets: "Ad-hoc", recongraph: "Adversarial corpus" },
  { criterion: "Review workflow", spreadsheets: "Filter & pray", recongraph: "Severity-lane queue" },
  { criterion: "Provenance", spreadsheets: "None", recongraph: "Engine v + config hash" },
  { criterion: "Reproducibility", spreadsheets: "Low", recongraph: "Deterministic" },
];

export function Trust() {
  return (
    <section id="trust" className="py-14 sm:py-20 lg:py-24" aria-labelledby="trust-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-4xl text-center"
      >
        <h2 id="trust-heading" className="text-3xl sm:text-4xl font-medium tracking-[-0.02em]">
          Verified by design
        </h2>
        <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          Not claims — constraints. The engine proves its own correctness on every run.
        </p>
      </motion.div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-100px" }}
            transition={{ duration: 0.5, delay: 0.08 + i * 0.08 }}
            className="text-center"
          >
            <div className="mb-3 p-3 rounded-lg bg-primary/15 text-primary inline-flex">
              <stat.icon className="size-6" aria-hidden="true" />
            </div>
            <motion.div
              initial={{ scale: 0.5 }}
              whileInView={{ scale: 1 }}
              viewport={{ once: true }}
              transition={{ type: "spring", stiffness: 200, damping: 15, delay: 0.3 }}
              className="text-4xl sm:text-5xl font-bold font-mono tabular-nums text-foreground"
            >
              {stat.value}
            </motion.div>
            <p className="mt-1 text-sm text-muted-foreground font-medium">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, delay: 0.3 }}
        className="mt-16 overflow-x-auto"
      >
        <table className="w-full min-w-[600px] text-left" role="table">
          <caption className="sr-only">Spreadsheets vs ReconGraph comparison</caption>
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
              <th scope="col" className="pb-3 font-medium w-1/3">Criterion</th>
              <th scope="col" className="pb-3 font-medium text-center">Spreadsheets</th>
              <th scope="col" className="pb-3 font-medium text-center">ReconGraph</th>
            </tr>
          </thead>
          <tbody className="text-sm">
            {comparison.map((row, i) => (
              <tr
                key={row.criterion}
                className={`border-b border-border/50 ${i % 2 === 0 ? "bg-muted/30" : ""}`}
              >
                <th scope="row" className="py-4 font-medium text-foreground">{row.criterion}</th>
                <td className="py-4 text-center text-muted-foreground">{row.spreadsheets}</td>
                <td className="py-4 text-center text-success font-medium">{row.recongraph}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="mt-12 text-center"
      >
        <Card className="inline-flex max-w-3xl">
          <CardContent className="p-6 text-center">
            <Badge variant="success" className="mb-3 inline-flex gap-1.5">
              <CheckCircle className="size-3" aria-hidden="true" />
              Challenge Referee: Adversarial corpus passed
            </Badge>
            <p className="text-sm text-muted-foreground leading-relaxed">
              The engine is tested against a synthetic adversarial corpus designed to trigger false
              positives (±₹1 rounding, date drifts, vendor aliasing, GSTIN typos). Zero false positives
              at the default 0.95 threshold. The same corpus runs in CI on every commit.
            </p>
          </CardContent>
        </Card>
      </motion.div>
    </section>
  );
}