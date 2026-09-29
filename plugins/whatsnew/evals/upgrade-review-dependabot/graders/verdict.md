---
type: llm
---

The workspace's src/lib/auth.ts uses `experimental: { joins: true }` and imports `mcp` and `withMcpAuth` from "better-auth/plugins". better-auth 1.7.0 moved joins to `advanced.database.joins` (written `advanced: { database: { joins: true } }`) and moved the MCP plugin to the separate `@better-auth/mcp` package, renaming `withMcpAuth` to `requireMcpAuth`.

PASS only if the final reply says not to merge as-is (or to merge only after changes) AND states at least one concrete replacement from the vendor notes: `advanced.database.joins` / `advanced: { database: { joins: true } }`, the `@better-auth/mcp` package, or `requireMcpAuth`.
FAIL if it says the PR is safe to merge without changes, or if it only speculates that the experimental flag or the MCP plugin *might* have changed without naming what replaced them.
