#!/usr/bin/env bash
# A workspace that uses both better-auth 1.7.0 breaking changes the mock returns.
set -euo pipefail
mkdir -p src/lib
cat > package.json <<'JSON'
{
  "name": "acme-web",
  "private": true,
  "dependencies": { "better-auth": "^1.7.0", "next": "16.3.6" }
}
JSON
cat > src/lib/auth.ts <<'TS'
import { betterAuth } from "better-auth";
import { mcp, withMcpAuth } from "better-auth/plugins";
import { db } from "./db";

export const auth = betterAuth({
  database: db,
  experimental: { joins: true },
  plugins: [mcp({ loginPage: "/sign-in", oidcConfig: { loginPage: "/sign-in" } })],
});

export const protect = withMcpAuth;
TS
