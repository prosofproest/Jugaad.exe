import type { Metadata } from "next";

import { AppShell } from "@/components/workspace/app-shell";
import { WorkspaceProvider } from "@/lib/workspace/store";

import "./globals.css";
import "./workspace.css";

export const metadata: Metadata = {
  title: {
    default: "CropSentinel · Pest & disease network",
    template: "%s · CropSentinel",
  },
  description:
    "Assistive photo assessment, farm health maps and verified pest hotspots. Not a diagnosis, not a confirmed outbreak.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main-content">
          Skip to content
        </a>
        <WorkspaceProvider>
          <AppShell>
            <div id="main-content">{children}</div>
          </AppShell>
        </WorkspaceProvider>
      </body>
    </html>
  );
}
