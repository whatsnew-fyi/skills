---
id: "2026-09.d3hx"
slug: the-product-skills-ship-as
title: "the product skills ship as one plugin under plugins, not in .agents/skills"
date: 2026-09-28
topics: [layout, distribution]
---

# ADR 2026-09.d3hx — the product skills ship as one plugin under plugins, not in .agents/skills

Status: Accepted (2026-09-28)

**Context:** this repository has two kinds of skill, and they are easy to confuse.
The product skills (`upgrade-review`, `outdated-audit`) are what the repository
publishes: people install them into their own agents. The dotagents layout also
reserves `.agents/skills/` for procedures an agent runs *while maintaining this
repository*, and some agents load that directory as the repo's own skills. Putting
the product skills there would make every contributor's agent fire `upgrade-review`
on this repo's own work, and would mix the payload with the tooling.

The plugin could also have sat at the repository root, with the marketplace and the
plugin sharing one `.claude-plugin/`. That makes the plugin root and the repo root the
same directory: every install would copy `AGENTS.md`, `.agents/`, `tests/` and CI into
the plugin cache, and `claude plugin validate` warns about a `CLAUDE.md` at a plugin
root, which `--strict` turns into a failure.

**Decision:** the marketplace lives at the root (`.claude-plugin/marketplace.json`), and
the one plugin, `whatsnew`, lives at `plugins/whatsnew/` with its skills under
`plugins/whatsnew/skills/<id>/`, its MCP server in `plugins/whatsnew/.mcp.json`, and its
evals in `plugins/whatsnew/evals/`. `.agents/skills/` stays reserved for maintenance
procedures, and is absent until one exists.

Both install paths were checked against this layout on 2026-09-28:
`claude plugin marketplace add` + `claude plugin install whatsnew@whatsnew-fyi` loaded
two skills and one MCP server, and `npx skills add <repo> --list` found both skills
under `plugins/`.

**Consequences / limits:** install ids are `whatsnew@whatsnew-fyi`, and the skills run as
`/whatsnew:upgrade-review` and `/whatsnew:outdated-audit`. Renaming the plugin, the
marketplace or a skill directory changes what users typed to install it, so treat those
names as public API. `claude plugin validate --strict` runs on both the root and
`plugins/whatsnew` in CI.
