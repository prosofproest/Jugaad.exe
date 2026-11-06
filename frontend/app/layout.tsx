import type { Metadata } from "next";
import Link from "next/link";

import { SidebarNav } from "@/components/sidebar-nav";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "PS-03 — Crop early warning",
    template: "%s — PS-03",
  },
  description:
    "Assistive photo assessment and area outlook. Not a diagnosis, not a confirmed outbreak.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <div className="app-shell">
          <aside className="app-sidebar">
            <Link href="/" className="app-brand" aria-label="PS-03 overview">
              <span className="app-brand-mark">PS-03</span>
              <span className="app-brand-text">
                <span className="app-brand-title">Crop early warning</span>
                <span className="app-brand-subtitle">
                  Decision support workspace
                </span>
              </span>
            </Link>

            <SidebarNav />

            <div className="app-sidebar-note">
              <span className="badge badge-muted">Phase 2 · scaffold</span>
              <p className="small muted">
                Demo paths are labelled. No image model or forecast is connected
                in this build.
              </p>
            </div>
          </aside>

          <div className="app-body">
            <header className="app-topbar">
              <p className="app-topbar-title">Crop early warning</p>
              <p className="app-topbar-meta small muted">
                Photo assessment and area outlook are separate outputs and are
                never merged.
              </p>
            </header>

            <main id="main-content" className="app-content">
              {children}
            </main>

            <footer className="site-footer">
              Decision support only. Photo assessment and area outlook are
              separate outputs and are never merged.
            </footer>
          </div>
        </div>
      </body>
    </html>
  );
}
