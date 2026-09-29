---
id: "2026-09.fm4r"
slug: each-skill-calls-the-mcp
title: "each skill calls the MCP server and falls back to a stdlib HTTP script"
date: 2026-09-28
topics: [mcp, portability]
---

# ADR 2026-09.fm4r — each skill calls the MCP server and falls back to a stdlib HTTP script

Status: Accepted (2026-09-28)

**Context:** the plugin bundles the What's New MCP server
(`https://whatsnew.fyi/mcp`), so a Claude Code or claude.ai user gets the tools with the
skills. A skill installed any other way (`npx skills add`, a copied folder, Codex or
Cursor) arrives without the server configured, and a skill that only says "call
`upgrade_notes`" does nothing there. The server is stateless and keyless: one POST of
a JSON-RPC `tools/call`, with no `initialize` first, answers with SSE-framed JSON.
This was measured against production on 2026-09-28.

**Decision:** each skill tells the agent to use the MCP tool when it is available, and
otherwise to run `scripts/whatsnew_call.py <tool>` with the tool's arguments on stdin.
That script makes the same call over plain HTTP and prints the tool's
`structuredContent`. It is Python 3.8+ standard library only, because `python3` is the
one runtime present across npm, PyPI, Go and .NET projects alike. A Node script would
strand the Go user, and a curl pipeline would leave the SSE parsing and error handling
to the model.

A skill installs on its own (`npx skills add --skill upgrade-review`), so the script is
**copied** into every skill that needs it rather than shared from one place.

**Consequences / limits:** the copies can drift. `tests/test_scripts.py` fails unless
every `whatsnew_call.py` is byte-identical, so edit one copy and copy it over the
others. Exit code 2 means the tool refused the input and 1 means transport failure.
The skills rely on that split, so keep it.
