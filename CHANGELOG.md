---
changelog: "0.1"
product:
  name: whatsnew skills
  vendor: whatsnew.fyi
  homepage: https://github.com/whatsnew-fyi/skills
  description: Agent skills that review dependency upgrades and audit outdated projects against vendor release notes.
  versioning: semver
  category: developer-tools
document:
  updated: 2026-09-28T00:00:00Z
  coverage: complete
  canonical: https://github.com/whatsnew-fyi/skills/blob/main/CHANGELOG.md
---

# whatsnew skills changelog

This file is a [Declarative Changelog](https://whatsnew.fyi/spec), validated in CI.

## [0.1.0](https://github.com/whatsnew-fyi/skills/releases/tag/v0.1.0) — 2026-09-28T00:00:00Z

> First release: a Claude Code plugin marketplace with two skills backed by the What's New MCP server.

### Added

- `upgrade-review` skill that checks a dependency upgrade against the vendor's verbatim breaking-change, migration, deprecation and security notes for every release in between, then searches the codebase for each affected identifier.
- `outdated-audit` skill that turns an npm, pnpm, yarn, pip, uv, Go, Cargo or .NET outdated report into a ranked list of missing security fixes, CVEs and bug fixes, split by whether a plain update reaches them.
- `whatsnew` plugin in the `whatsnew-fyi` marketplace, bundling both skills and the What's New MCP server.
- `whatsnew_call.py` fallback that calls the MCP tools over plain HTTP, for agents with no MCP client.
- `outdated_to_deps.py` converter that batches outdated reports into tool arguments and leaves workspace and private-registry packages out.
