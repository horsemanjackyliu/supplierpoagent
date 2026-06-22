/** @type {import('next').NextConfig} */
const nextConfig = {
  // Agent base URL injected at build time or via NEXT_PUBLIC_ env var at runtime
  env: {
    NEXT_PUBLIC_AGENT_URL: process.env.NEXT_PUBLIC_AGENT_URL || 'https://27c30ede-2a17e47f.sap3eu12.c.run.ai.cloud.sap',
  },
}

module.exports = nextConfig
