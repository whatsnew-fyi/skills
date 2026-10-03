# What's New skills

**Agent skills that read the release notes before you upgrade, and help you write your own.**

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
| [`declarative-changelog`](plugins/whatsnew/skills/declarative-changelog/SKILL.md) | *Does our changelog say what changed, in a form both a reader and a parser get right?* | cutting a release, writing a changelog entry from commits, or converting an existing `CHANGELOG.md` so bots and aggregators read it correctly |

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

**`declarative-changelog`** works on the other end of release notes: your own. It
converts a `CHANGELOG.md` to the [Declarative Changelogs](https://whatsnew.fyi/spec)
format, which is Keep a Changelog with YAML frontmatter, a strict release-heading
grammar and an exact `**Breaking**` marker, so tools stop guessing at your versions,
dates and breaking changes. It drafts new entries from your Conventional Commits,
rewrites them for readers, writes the one-sentence summary (or asks you when the
commits don't make the point of a release clear), and runs the
`declarative-changelog` validator until the file is clean.

`upgrade-review` and `outdated-audit` get their data from
[What's New](https://whatsnew.fyi), which tracks the release history of more than a
thousand packages, apps and tools and serves it over a public
[MCP server](https://whatsnew.fyi/mcp/setup). No API key, no sign-in.
`declarative-changelog` runs locally and needs no server.

## Install

### Claude Code

Add the marketplace, then install the plugin. It brings all three skills and
connects the MCP server.

```text
/plugin marketplace add whatsnew-fyi/skills
/plugin install whatsnew@whatsnew-fyi
```

### Codex, Cursor, Gemini CLI and other Agent Skills agents

```sh
npx skills add whatsnew-fyi/skills
```

Add `--skill upgrade-review`, `--skill outdated-audit` or
`--skill declarative-changelog` to install just one.

Installed this way, the dependency skills reach the server through a small bundled script
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
- *"Add the 2.0.0 release to CHANGELOG.md from the commits since v1.4.0."*
- *"Convert our CHANGELOG.md to a declarative changelog."*

In Claude Code you can also run them directly:

```text
/whatsnew:upgrade-review
/whatsnew:outdated-audit
/whatsnew:declarative-changelog
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

### Declarative changelog

A release entry drafted from Conventional Commits (`feat`, `fix`, `feat!`, `chore`),
after the agent rewrote the items for readers and wrote the summary:

```markdown
## [2.0.0](https://github.com/acme/kestrel/releases/tag/v2.0.0) — 2026-09-28T14:02:00Z

> JSON output for every command, and Node 18 is no longer supported.

### Added

- Every command accepts `--json` for machine-readable output. (#212)

### Removed

- **Breaking** — Node.js 18 is no longer supported. Kestrel now requires Node.js 20 or later.

### Fixed

- `kestrel init` no longer crashes when the config file is empty. (#207)
```

The validator then reports `Level 2 — Categorized · 14 entries · addressable`.

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
ecosystem. `declarative-changelog` works on any project with a `CHANGELOG.md`; its
draft script reads any git history written as Conventional Commits.

## How it works

The dependency skills call two tools on the What's New MCP server:

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

`declarative-changelog` calls no server. Its draft script (`draft_entry.py`) reads
`git log` and maps commit types to changelog categories using the spec's table. The
[`declarative-changelog`](https://www.npmjs.com/package/declarative-changelog) validator
runs through `npx`, so that skill needs Node.js 20 or later.

## What leaves your machine

The skills' own network traffic goes to two places: `whatsnew.fyi`, for release
data, and the npm registry, to fetch the changelog validator.

The dependency skills send `whatsnew.fyi`:

- package names, their registry, and version numbers: installed, newest in range,
  and newest published;
- for npm packages, each package's public source-repository URL, and for Go and
  NuGet packages, a package URL (purl). Both make the match exact.

They send no source code, file paths or anything that names your project. Requests
from the fallback script carry a User-Agent that names the skills' version.

Private packages stay local. The converter drops npm workspace and private-registry
packages on its own. For anything else internal, in any ecosystem, it takes
`--exclude '@yourorg/*'`, and the agent leaves out the packages you name as internal.

When a Maven, Go or NuGet package isn't tracked yet, the server checks the name
against deps.dev and counts the miss per day, with nothing about the caller, to
decide what to track next. To turn that off, ask your agent to pass
`"recordMisses": false`.

The skills also fetch two things: `upgrade-review` reads a `whatsnew.fyi`
compare page, as markdown, when a result was cut short, and `declarative-changelog`
runs its validator with `npx -y declarative-changelog@0.2.0`, which downloads it from
npm.

## What the skills won't do

- **Change your code or run installers.** They review and audit. Updating is your
  call, and they give you the exact command. The one file a skill edits is the
  changelog you ask `declarative-changelog` to write.
- **Invent release facts.** `declarative-changelog` leaves out a date, version or
  link it can't find in your repository, and tells you which ones.
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

Found a package What's New should track? Suggest it at [whatsnew.fyi/suggest](https://whatsnew.fyi/suggest).

## License

[MIT](LICENSE)
