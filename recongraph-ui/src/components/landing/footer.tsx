"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { GitBranch, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function Footer() {
  const year = new Date().getFullYear();

  const links = {
    Product: [
      { label: "Features", href: "#features" },
      { label: "How it works", href: "#how-it-works" },
      { label: "Trust & Proof", href: "#trust" },
      { label: "FAQ", href: "#faq" },
    ],
    Resources: [
      { label: "Documentation", href: "/docs" },
      { label: "Changelog", href: "/changelog" },
      { label: "API Reference", href: "/api" },
    ],
    Legal: [
      { label: "Privacy", href: "/privacy" },
      { label: "Terms", href: "/terms" },
      { label: "License (AGPL-3.0)", href: "/license" },
    ],
  };

  return (
    <footer className="border-t border-border pt-10 pb-8" role="contentinfo">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="grid gap-8 md:grid-cols-[auto_1fr_auto] items-start"
      >
        <div className="flex flex-col items-start gap-4 md:items-center">
          <Link href="/" className="flex items-center gap-2" aria-label="ReconGraph home">
            <span className="text-xl font-bold tracking-tight text-foreground">
              Recon<span className="text-primary">Graph</span>
            </span>
          </Link>
          <p className="text-xs text-muted-foreground max-w-xs">
            Deterministic GST reconciliation engine. V1 Certified Core.
          </p>
          <div className="flex items-center gap-4">
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors" aria-label="GitHub">
              <GitBranch className="size-5" />
            </a>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-muted-foreground hover:text-foreground transition-colors" aria-label="Twitter">
              <FileText className="size-5" />
            </a>
          </div>
        </div>

        <nav className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" aria-label="Footer navigation">
          {Object.entries(links).map(([category, items]) => (
            <div key={category}>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                {category}
              </h4>
              <ul className="space-y-2" role="list">
                {items.map((item) => (
                  <li key={item.label}>
                    <Link
                      href={item.href}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        <div className="flex flex-col items-end gap-4 md:items-center text-right">
          <p className="text-xs text-muted-foreground">
            Built with Next.js, React, and deterministic graph theory.
          </p>
          <Badge variant="neutral" className="text-xs">
            AGPL-3.0
          </Badge>
          <p className="text-xs text-muted-foreground">
            © {year} ReconGraph. Open source reconciliation.
          </p>
        </div>
      </motion.div>
    </footer>
  );
}