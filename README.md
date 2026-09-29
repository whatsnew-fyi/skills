# What's New skills

**Agent skills that read the release notes before you upgrade.**

[![CI](https://github.com/whatsnew-fyi/skills/actions/workflows/ci.yml/badge.svg)](https://github.com/whatsnew-fyi/skills/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![MCP server](https://img.shields.io/badge/MCP-whatsnew.fyi%2Fmcp-555)](https://whatsnew.fyi/mcp/setup)

A Dependabot PR that bumps a minor version looks safe. Often it is. Sometimes the
vendor's notes for that release say a plugin moved to its own package, or a config
key was renamed, and you learn it from a failing deploy. These skills read those
notes for you, for every release in the range, and check them against your code.

- [The skills](#the-skills)
- [Install](#install)
- [Use](#use)
- [Examples](#examples)
- [Supported ecosystems](#supported-ecosystems)
- [How it works](#how-it-works)
- [What leaves your machine](#what-leaves-your-machine)
- [What the skills won't do](#what-the-skills-wont-do)
- [Contributing](#contributing)

## The skills

| Skill | Answers | Reach for it when |
| --- | --- | --- |
| [`upgrade-review`](plugins/whatsnew/skills/upgrade-review/SKILL.md) | *What has to change in this codebase before the upgrade is safe to merge?* | reviewing a Dependabot or Renovate PR, bumping a package, SDK, framework or GitHub Action, or planning a major-version move |
| [`outdated-audit`](plugins/whatsnew/skills/outdated-audit/SKILL.md) | *What is this project missing by being behind, and what should we update first?* | you have a pile of outdated dependencies and limited time, or you want to know which security fixes you don't have yet |

**`upgrade-review`** collects the vendor's own breaking-change, migration,
deprecation and security notes for every release between your version and the
target, quotes them verbatim, and then finds the lines in your code that each note
affects. It flags breaking changes that ship in minor and patch versions, which is
where they are easiest to miss.

**`outdated-audit`** turns `npm outdated` (or the pip, uv, Go, Cargo or .NET
equivalent) into a ranked list of the security fixes, CVEs and bug fixes your
project doesn't have yet. It splits them into what a plain update reaches inside
your declared version ranges and what needs a manifest change, and puts the cost of
each move beside it: major bumps, breaking changes, removals.

Both get their data from [What's New](https://whatsnew.fyi), which tracks the
release history of more than a thousand packages, apps and tools and serves it over
a public [MCP server](https://whatsnew.fyi/mcp/setup). No API key, no sign-in.

## Install

### Claude Code

Add the marketplace, then install the plugin. It brings both skills and connects
the MCP server.

```text
/plugin marketplace add whatsnew-fyi/skills
/plugin install whatsnew@whatsnew-fyi
```

### Codex, Cursor, Gemini CLI and other Agent Skills agents

```sh
npx skills add whatsnew-fyi/skills
```

Add `--skill upgrade-review` or `--skill outdated-audit` to install just one.

Installed this way, the skills reach the server through a small bundled script
(Python 3.8+, standard library only, no dependencies). If your agent speaks MCP, you
can also point its config at `https://whatsnew.fyi/mcp` so it calls the tools
directly.

### MCP only

Prefer to skip the skills? Any MCP client can use the tools on their own. The
[setup page](https://whatsnew.fyi/mcp/setup) has config snippets for the common
clients.

## Use

You don't need to name the skills. Ask the way you normally would:

- *"Dependabot wants to bump better-auth from 1.6.0 to 1.7.0. Can I just merge it?"*
- *"Review this Renovate PR."*
- *"What breaks if we move from Django 4.2 to 5.2?"*
- *"We're behind on dependencies. What should we update first?"*
- *"Are we missing any security fixes?"*

In Claude Code you can also run them directly:

```text
/whatsnew:upgrade-review
/whatsnew:outdated-audit
```

## Examples

### Upgrade review

From an eval run against better-auth's real 1.7.0 release notes:

```markdown
**No, don't merge it as-is.** In better-auth 1.7.0 the minor-version bump includes a
long list of breaking changes, and `src/lib/auth.ts` uses several of them.

**Blocking 1: the MCP plugin has moved out of `better-auth`.**
> **Migration:** Install `@better-auth/mcp` and `@better-auth/cimd`, add the
> now-required `jwt()` plugin, … Rename `withMcpAuth` to `requireMcpAuth` …
- `src/lib/auth.ts:2` imports `mcp` and `withMcpAuth` from `better-auth/plugins`.
  That import needs to come from `@better-auth/mcp` instead.

**Blocking 2: the joins option has moved.**
> **Migration:** Replace `experimental: { joins: true }` with
> `advanced: { database: { joins: true } }`. …
- `src/lib/auth.ts:7` uses `experimental: { joins: true }`.
```

### Outdated audit

What the report looks like, filled in with data recorded from production for an
npm project three packages behind:

```markdown
## 1 of 3 outdated packages is missing security fixes

**Fix now, no manifest change** (`npm update next`)
- **next** 16.2.0 → 16.3.6: 4 security fixes, CVE-2025-13465
  - "Fix Remote Code Execution vulnerability in next/og ImageResponse (GHSA-vcvr-r3jv-pc5j)" (v16.3.6)
  - "Fix unauthenticated remote code execution on windows-hosted servers" (v16.3.3)
  - [all 9 releases](https://whatsnew.fyi/product/next-js/compare/16.2.0...v16.3.6)

**Bug fixes only:** better-auth (12 in range; 6 more in 1.7.x, with 2 removals)
**Untracked (1):** left-pad-nope
```

## Supported ecosystems

| | `upgrade-review` | `outdated-audit` |
| --- | --- | --- |
| npm | yes | yes (npm, pnpm, yarn 1) |
| PyPI | yes | yes (pip, uv) |
| Go modules | yes | yes |
| crates.io | yes | yes (with `cargo-outdated`) |
| NuGet | yes | yes |
| Maven / Gradle | yes | entries built by hand |
| RubyGems | yes | entries built by hand |
| GitHub Actions | yes | |

A package What's New doesn't track yet is reported as untracked, whatever its
ecosystem.

## How it works

The skills call two tools on the What's New MCP server:

- **`upgrade_notes`** returns the vendor's breaking-change, migration, deprecation
  and security sections verbatim, for every tracked release between two versions,
  with a link to each release's source notes. The skill quotes them and searches
  your code for what they name.
- **`missing_changes`** counts the security fixes, CVEs and bug fixes between your
  installed version, the newest version your range allows, and the newest version
  published. The counts are computed from tracked releases, not judged by a model.

A bundled converter (`outdated_to_deps.py`) reads the outdated report from your
package manager, batches it into tool calls, and adds what the server needs for an
exact match.

## What leaves your machine

The skills send `whatsnew.fyi` package names, version numbers and, for npm, each
package's public source-repository URL (which makes the match exact). They send no
source code, file paths or anything that names your project.

Private packages stay local. The converter drops npm workspace and private-registry
packages on its own, and takes `--exclude '@yourorg/*'` for anything else internal.

When a Maven, Go or NuGet package isn't tracked yet, the server counts the miss per
day, with nothing about the caller, to decide what to track next. To turn that off,
ask your agent to pass `"recordMisses": false`.

## What the skills won't do

- **Change your code or run installers.** They review and audit. Updating is your
  call, and they give you the exact command.
- **Call an upgrade safe on missing data.** A package What's New doesn't track is
  reported as untracked, never as fine. For those, check the vendor's changelog.
- **Replace a vulnerability scanner.** The security counts come from what vendors
  wrote in their release notes. Pair the audit with `npm audit`, OSV or your
  scanner of choice.

## Contributing

This repository follows the [dotagents](https://github.com/bgreenwell/dotagents)
layout. [`AGENTS.md`](AGENTS.md) routes agents and people to the rules, context and
decisions under `.agents/`.

```text
.claude-plugin/marketplace.json   the whatsnew-fyi marketplace
plugins/whatsnew/                 the plugin: skills, .mcp.json and evals
tests/                            unit tests for the skills' scripts
.agents/                          context for working on this repo (not shipped)
```

The checks, the evals and how to try a skill against production are in
[`.agents/context/commands.md`](.agents/context/commands.md). Changes are recorded
in [`CHANGELOG.md`](CHANGELOG.md).

Found a package What's New should track? Suggest it at [whatsnew.fyi](https://whatsnew.fyi).

## License

[MIT](LICENSE)
