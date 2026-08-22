"use client";

import Link from "next/link";
import { motion } from "motion/react";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";
import { useState, useEffect } from "react";

export function Nav() {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const links = [
    { href: "#problem", label: "Problem" },
    { href: "#how-it-works", label: "How it works" },
    { href: "#features", label: "Features" },
    { href: "#trust", label: "Trust" },
    { href: "#faq", label: "FAQ" },
  ];

  return (
    <>
      <nav
        className={`sticky top-0 z-50 flex h-16 items-center justify-between transition-all duration-200 ${
          isScrolled ? "bg-background/80 backdrop-blur-md border-b border-border" : ""
        }`}
      >
        <Link href="/" className="flex items-center gap-2" aria-label="ReconGraph home">
          <span className="text-xl font-bold tracking-tight text-foreground">
            Recon<span className="text-primary">Graph</span>
          </span>
        </Link>

        <div className="hidden md:flex md:items-center md:gap-6">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {link.label}
            </Link>
          ))}
          <div className="flex items-center gap-3 ml-4">
            <Link href="/app" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors hidden sm:inline-block">
              Open App
            </Link>
            <Button size="sm" asChild>
              <Link href="/app?demo=1">Try Demo</Link>
            </Button>
          </div>
        </div>

        <div className="md:hidden flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => setIsMobileOpen(!isMobileOpen)} aria-label={isMobileOpen ? "Close menu" : "Open menu"} aria-expanded={isMobileOpen}>
            {isMobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </nav>

      {isMobileOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden overflow-hidden bg-background border-b border-border"
        >
          <div className="px-4 py-4 space-y-3">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block py-2 text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
                onClick={() => setIsMobileOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="flex flex-col gap-2 pt-2 border-t border-border">
              <Link href="/app" className="text-base font-medium text-muted-foreground hover:text-foreground transition-colors" onClick={() => setIsMobileOpen(false)}>
                Open App
              </Link>
              <Button className="w-full" asChild>
                <Link href="/app?demo=1">Try Demo</Link>
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </>
  );
}