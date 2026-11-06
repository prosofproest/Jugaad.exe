import path from "node:path";

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Pin the workspace root: an unrelated lockfile in a parent directory must
  // never be picked up as the build root.
  turbopack: {
    root: path.resolve(process.cwd()),
  },
  // The web app is an API-only client: it never connects to the database.
  // See final/docs-context/architecture-context.md and ADR-003.
};

export default nextConfig;
