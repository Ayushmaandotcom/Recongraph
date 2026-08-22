"use client";

import { motion } from "motion/react";
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from "@/components/ui/accordion";

const faqs = [
  {
    q: "What evidence types does ReconGraph support?",
    a: "Currently: Purchase Register (CSV), GSTR-2B (JSON), with extensible adapters for invoices and bank statements planned. The engine treats every record as evidence describing an underlying financial event — it doesn't assume the document is the event itself.",
  },
  {
    q: "How is the 0.95 threshold determined?",
    a: "Calibrated on the Challenge Referee adversarial corpus: 10,000+ synthetic cases covering ±₹1 rounding, date drifts (±3 days), vendor name aliases, GSTIN typos, and reference format variations. The threshold maximizes true positive throughput while holding false positives at zero.",
  },
  {
    q: "What does 'strict conservation' mean?",
    a: "For every reconciliation run: count(input records) === count(output records). Every input record appears exactly once in the output — either in an auto-matched pair, or in a review packet. No record is ever dropped, duplicated, or merged silently.",
  },
  {
    q: "What are the three review severities?",
    a: "&bull; <strong>Ambiguous</strong>: Multiple candidate counterparts above threshold &mdash; human must choose.<br/>&bull; <strong>Weak Evidence</strong>: Single candidate below 0.95 but above noise floor &mdash; likely match with insufficient signal.<br/>&bull; <strong>Leftover</strong>: No counterpart found &mdash; potentially missing GST record or orphan PR entry.",
  },
  {
    q: "Does ReconGraph auto-post to accounting systems?",
    a: "No. ReconGraph is an investigation engine, not a posting engine. It produces review packets and resolution proposals. Human approval is required before any external system mutation. The engine version and config hash on every result enable audit trails.",
  },
  {
    q: "Can I run this on my own data?",
    a: "Yes. The demo loads the static Challenge Referee corpus. For your data, deploy the FastAPI backend (<code>recongraph-api</code>) and point the UI at <code>http://localhost:8000/reconcile</code>. The UI falls back to the static demo if the backend isn't available.",
  },
  {
    q: "What's the difference from fuzzy matching?",
    a: "Fuzzy matching gives a single similarity score. ReconGraph emits a <strong>Financial Relationship Score</strong> composed of five explainable signals (entity, reference, amount, temporal, tax-identity) with per-signal contributions and a semantic finding classification (missing vs contradictory). You see <em>why</em>, not just <em>how much</em>.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="py-14 sm:py-20 lg:py-24" aria-labelledby="faq-heading">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="mx-auto max-w-3xl text-center"
      >
        <h2 id="faq-heading" className="text-3xl sm:text-4xl font-medium tracking-[-0.02em]">
          Questions you&apos;ll ask
        </h2>
        <p className="mt-4 text-lg text-muted-foreground leading-relaxed">
          Honest answers for engineers and auditors evaluating the engine.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.6, delay: 0.1 }}
        className="mt-10 mx-auto max-w-3xl"
      >
        <Accordion type="single" collapsible className="space-y-3">
          {faqs.map((faq, i) => (
            <AccordionItem key={i} value={String(i)}>
              <AccordionTrigger className="text-left px-1">
                <span className="text-base font-medium text-foreground">{faq.q}</span>
              </AccordionTrigger>
              <AccordionContent>
                <div dangerouslySetInnerHTML={{ __html: faq.a }} className="text-sm text-muted-foreground leading-relaxed" />
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </motion.div>
    </section>
  );
}