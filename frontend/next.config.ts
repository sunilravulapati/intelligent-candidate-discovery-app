import type { NextConfig } from "next";

/**
 * Next.js configuration.
 *
 * API proxying is now handled by the runtime API route at:
 *   src/app/api/[...path]/route.ts
 *
 * That route reads BACKEND_URL at request time (not build time), so you can
 * update the backend URL on Vercel's dashboard and redeploy from cache without
 * any code changes.
 *
 * Previously, this file used next rewrites() which baked BACKEND_URL into the
 * edge config at build time — requiring a full rebuild on every URL change.
 */
const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;

