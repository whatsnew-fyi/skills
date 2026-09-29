---
id: "2026-09.vyb9"
slug: the-whatsnew-plugin-also-ships
title: "the whatsnew plugin also ships a publisher skill that needs no MCP server"
date: 2026-09-28
topics: [scope, layout]
---

# ADR 2026-09.vyb9 — the whatsnew plugin also ships a publisher skill that needs no MCP server

Status: Accepted (2026-09-28)

**Context:** the first two skills (`upgrade-review`, `outdated-audit`) consume release
notes: they ask the What's New MCP server what vendors wrote. The
[Declarative Changelogs](https://whatsnew.fyi/spec) standard, drafted in `whatsnew-app`,
covers the other side: a `CHANGELOG.md` a publisher writes so that no consumer has to
guess. Its reference validator is the `declarative-changelog` npm package (0.2.0 on
2026-09-28, two commands, `validate` and `parse`). Nothing helped an agent adopt the
format or write an entry in it. A skill for that is a publisher tool. It makes no MCP
call, it edits a file in the user's repository, and it needs Node for the validator.
Each of those breaks an assumption the first two skills were written under.

**Decision:** `declarative-changelog` ships in the existing `whatsnew` plugin, at
`plugins/whatsnew/skills/declarative-changelog/` (ADR 2026-09.d3hx). The alternative was
a second plugin in the `whatsnew-fyi` marketplace with no `.mcp.json`. It was rejected
because it adds a second install name and a second eval suite, while publishers and
consumers of changelogs are largely the same developers. `npx skills add --skill
declarative-changelog` already installs the skill on its own.

Three rules follow for this skill only:

- **It edits the changelog, and nothing else.** The agent writes the `CHANGELOG.md` the
  user asked about. Its script, `draft_entry.py`, still never writes. It runs a
  read-only `git log` and prints a draft, so the script rule in `skill-authoring.md`
  holds unchanged.
- **Validation needs Node.** The validator is TypeScript and has no Python port. Unlike
  `whatsnew_call.py` (ADR 2026-09.fm4r), there is no stdlib fallback. Without Node the
  skill applies `references/format.md` by hand, and says it did not validate.
- **The format is a draft someone else owns.** The spec's source of truth is
  `whatsnew-app` (`src/app/spec/content.md`), and the validator's closed vocabularies
  live in its `src/constants.ts`. `references/format.md` summarizes both and is
  refreshed when either changes. The skill pins `declarative-changelog@0.2`.

**Consequences / limits:** the plugin is no longer "skills backed by the MCP server".
Its description, the README and `AGENTS.md` say it also helps publish release notes. A
reader who assumes every skill here makes MCP calls, or that no skill writes files, is
now wrong about this one. The skill's evals grant read-only tools (ADR 2026-09.dqcj), so
they grade the document the agent proposes, not a written file. The validator pin moves
by hand, together with the CI pin in both CI files. `tests/test_scripts.py`
(`DraftEntry`) keeps the Conventional Commits mapping in `draft_entry.py` true to the
spec's table.
