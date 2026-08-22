import type { Metadata } from "next";
import { Fira_Sans, Fira_Code } from "next/font/google";
import "./globals.css";

const firaSans = Fira_Sans({
  variable: "--font-fira-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const firaCode = Fira_Code({
  variable: "--font-fira-code",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "ReconGraph — GST Reconciliation Engine",
  description:
    "Deterministic graph-based reconciliation for Indian GST compliance. Every match proven, every conflict explained, zero data loss.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${firaSans.variable} ${firaCode.variable} antialiased min-h-screen bg-[var(--color-background)] text-[var(--color-text)]`}
      >
        {children}
      </body>
    </html>
  );
}
