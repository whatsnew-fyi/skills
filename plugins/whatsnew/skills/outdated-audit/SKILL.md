---
name: outdated-audit
description: >-
  Audit a whole project's outdated dependencies and report what it is missing,
  most exposed first: the security releases, CVE fixes and bug fixes it
  doesn't have yet, split between what a plain update reaches inside the
  declared version ranges and what needs a manifest change, with the cost of
  each move (major bumps, breaking changes, removals). Use when asked what's
  outdated, how far behind the project is, whether it's missing security
  fixes or CVEs, which dependencies to update first, or to plan or prioritize
  dependency updates; and when given the output of npm/pnpm/yarn outdated, pip
  or uv `list --outdated`, `go list -m -u`, `cargo outdated` or `dotnet list
  package --outdated`.
license: MIT
compatibility: >-
  Uses the What's New MCP server (https://whatsnew.fyi/mcp, no key). The
  bundled scripts need python3; without the MCP server they also need network
  access to whatsnew.fyi.
---

# Outdated audit

`npm outdated` says a project is behind. It doesn't say what being behind
costs. This skill answers that. For every outdated package it reports which
security fixes, CVEs and bug fixes the project doesn't have yet, whether a
plain update can reach them, and what moving would break.

The answers come from [What's New](https://whatsnew.fyi), which tracks release
history for more than a thousand packages. Its `missing_changes` tool counts what shipped
between the installed version and the newer ones, over every tracked release.
Those counts are deterministic: no model judges anything.

## 1. Get the outdated report

Find the project's ecosystems from their lockfiles, then run the matching
command from the project root. All of these are read-only:

| Ecosystem | Command |
| --- | --- |
| npm | `npm outdated --json > outdated.json` (exit 1 means "something is outdated", not a failure) |
| pnpm | `pnpm outdated --format json > outdated.json` |
| yarn 1 | `yarn outdated --json > outdated.json` |
| pip | `pip list --outdated --format json > outdated.json`, inside the project's virtualenv |
| uv | `uv pip list --outdated --format json > outdated.json` |
| Go | `go list -m -u -json all > outdated.json` |
| Cargo | `cargo outdated --format json > outdated.json` (needs `cargo-outdated`) |
| .NET | `dotnet list package --outdated --format json > outdated.json` |

Write the report to a scratch or temp path, not into the repository. If the
user has pasted a report, use theirs. If a command isn't installed, say so and
move on to the other ecosystems. Don't install tools unasked.

For other ecosystems (Gradle's versions report, Maven's `versions:display-dependency-updates`,
Composer, Bundler), build the dependencies by hand in the shape shown in step 2.

## 2. Convert it

```sh
python3 scripts/outdated_to_deps.py outdated.json --exclude '@yourorg/*'
```

The script detects the format and prints one line per batch of at most 100
dependencies. Each line is a complete `missing_changes` argument object. It
also adds what the tool needs to match packages exactly: the npm `repository`
from `node_modules`, and the purl for Go and NuGet packages.

**Private packages stay on the machine.** The script drops npm workspace and
private-registry packages by itself. Pass `--exclude` for anything else that's
internal, such as your org's scope or an internal fork. Its stderr summary
lists every skipped package, so tell the user which ones were left out.

Built by hand, one entry looks like this. `from` is the installed version.
`wanted` is the newest version the declared range admits. `latest` is the
newest version published.

```json
{"name": "next", "from": "16.2.0", "wanted": "16.3.6", "latest": "16.3.6"}
```

## 3. Call `missing_changes`

Make one call per batch line.

**If the What's New MCP tools are available** (their names end in
`missing_changes`, `upgrade_notes`, `whats_new`), pass each line to
`missing_changes` as the arguments.

**If they aren't,** pipe each line to the bundled script, which makes the same
call over HTTP:

```sh
python3 scripts/outdated_to_deps.py outdated.json |
  while IFS= read -r batch; do
    printf '%s\n' "$batch" | python3 scripts/whatsnew_call.py missing_changes
  done
```

Exit 2 means the tool refused a batch, and stderr says why. Exit 1 is a network
or protocol failure.

## 4. Read the result

`summary` gives totals across the batch: `tracked`, `behindInRange`,
`withSecurity` and every `cves` id. Each package also has a `status`. An
`untracked` package isn't in the catalog, so count it and list it, but don't
guess what it's missing.

A tracked package has up to two blocks:

- **`toWanted`** covers `from` to `wanted`: what `npm update` (or the
  ecosystem's equivalent) brings **without editing the manifest**.
- **`toLatest`** covers the rest, up to `latest`, which needs the version range
  changed.

Each block carries these fields:

- `gain`: counts of `security` and `fixed` items, plus `cves`.
- `cost`: `majorBump`, `breakingMentions`, `removed` and `deprecated`.
- `items`: a few of the security fixes and bug fixes themselves, each tagged
  with its `versions`.
- `compareUrl`: the whole range on What's New.

A block with `releases: 0` and no gain means nothing tracked is waiting there.

## 5. Report, most exposed first

Rank the packages into these tiers and lead with the first non-empty one:

1. **Security fixes a plain update gets you.** These have `toWanted.gain.security`
   above 0 and are the cheapest risk reduction there is. Name the update
   command.
2. **Security fixes that need a range change.** These are security gains only in
   `toLatest`. Put the cost beside each one: a major bump, breaking mentions,
   removals.
3. **Bug fixes only.** One line each, grouped by whether a plain update or a
   range change reaches them.
4. **Nothing tracked waiting**, or **untracked.** Give a count and the names.

```markdown
## 3 of 17 outdated packages are missing security fixes

**Fix now, no manifest change** (`npm update next`)
- **next** 16.2.0 → 16.3.6: 4 security fixes, CVE-2025-13465
  - "Fix Remote Code Execution vulnerability in next/og ImageResponse" (v16.3.6)
  - [all 9 releases](https://whatsnew.fyi/product/next-js/compare/…)

**Needs a range change**
- **django** 4.2 → 6.1.1: 14 security fixes, 21 CVEs · major bump
  …

**Bug fixes only:** better-auth (12, in range), …
**Untracked (3):** @types/node, …
```

Quote fix text as it came back, and keep the version tags. Link each package's
`compareUrl`. Credit What's New (whatsnew.fyi) once, as the source of the
release data.

## 6. Offer the next step

End by offering to run an upgrade review on the packages worth moving.
`upgrade_notes`, on the same server, returns the vendor's verbatim
breaking-change and migration sections for exactly those moves. If the
`upgrade-review` skill is installed, it does the whole review.

## Rules

- **Don't update anything unasked.** This skill audits. Running `npm update`
  or editing a manifest is the user's call. Offer the exact command.
- **Counts are over tracked releases.** Say "no tracked security fixes", never
  "no security issues". The catalog isn't a vulnerability database, and a
  package it doesn't track tells you nothing either way.
- **Don't invent CVE details.** Report the ids and the vendor's fix text. For
  severity or affected configurations, link the advisory rather than guessing.
