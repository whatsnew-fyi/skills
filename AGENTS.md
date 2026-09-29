# AGENTS.md

## Identity

You maintain **What's New's public agent skills**: a Claude Code plugin marketplace
whose one plugin, `whatsnew`, ships Agent Skills that answer dependency questions from
the [What's New](https://whatsnew.fyi) MCP server, plus one publisher skill that writes
changelogs in the Declarative Changelogs format (ADR 2026-09.vyb9). People install these
into their own agents, so every skill must be useful to someone who has never heard of
What's New.

- `.claude-plugin/marketplace.json`: the marketplace (`whatsnew-fyi`).
- `plugins/whatsnew/`: the plugin, with its skills, `.mcp.json` and evals.
- `tests/`: unit tests for the skills' scripts, against real recorded reports.
- `.agents/`: context for working on this repo. It is not shipped.

## Context routing

- **Before editing a `SKILL.md` or a skill script:** READ
  [`.agents/rules/skill-authoring.md`](.agents/rules/skill-authoring.md).
- **If a change touches what a skill sends to the server or reads back:** READ
  [`.agents/context/mcp-tools.md`](.agents/context/mcp-tools.md).
- **If changing manifests, install names, versions, or cutting a release:** READ
  [`.agents/context/distribution.md`](.agents/context/distribution.md).
- **Before running checks or evals, and before calling a change finished:** READ
  [`.agents/context/commands.md`](.agents/context/commands.md).
- **Before touching any file:** MATCH the task against the trigger table in
  [`.agents/rules/decisions.md`](.agents/rules/decisions.md), and READ every ADR a
  matching row names.
- **If making an architectural or scope decision:** CONSULT
  [`.agents/memory/decisions.md`](.agents/memory/decisions.md), then record the new one
  per [`.agents/rules/decisions.md`](.agents/rules/decisions.md).

## Capabilities

- RUN the checks in [`.agents/context/commands.md`](.agents/context/commands.md).
- ADD a decision with `python3 scripts/adr.py new "<title>"`, then `index`.
- WRITE to `.agents/memory/`, which is read/write by design.

## Maintenance

This file is a **router**, not a store. Durable knowledge goes in `.agents/`: standing
rules in `rules/`, decisions in `memory/decisions/`, reference in `context/`. It never
goes here, and never into host-local agent memory. Add a routing line only when nothing
points at the new file yet.
