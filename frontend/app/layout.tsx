import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "PS-03 — Crop early warning",
  description:
    "Assistive photo assessment and area outlook. Not a diagnosis, not a confirmed outbreak.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <strong>PS-03</strong>
          <nav aria-label="Primary">
            <Link href="/">Overview</Link>
            <Link href="/chat">Photo assessment</Link>
          </nav>
        </header>
        <main>{children}</main>
        <footer className="site-footer">
          Decision support only. Photo assessment and area outlook are separate
          outputs and are never merged.
        </footer>
      </body>
    </html>
  );
}
