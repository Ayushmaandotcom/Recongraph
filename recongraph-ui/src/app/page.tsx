import type { Metadata } from "next";
import { LandingPage } from "@/components/landing/landing-page";

export const metadata: Metadata = {
  title: "ReconGraph — Deterministic GST Reconciliation Engine",
  description:
    "Prove every match. Explain every exception. Zero data loss. V1 certified core with Challenge Referee adversarial validation.",
  openGraph: {
    title: "ReconGraph — Deterministic GST Reconciliation",
    description:
      "Graph-based engine for PR vs GSTR-2B reconciliation. Auto-match at 0.95 threshold, strict conservation, human review queue.",
    type: "website",
  },
};

export default function Page() {
  return <LandingPage />;
}