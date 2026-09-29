---
name: upgrade-review
description: >-
  Review a dependency upgrade against the vendor's own release notes before it
  merges: breaking changes, migration steps, deprecations and CVE fixes across
  every release in between, including breaking changes shipped in a minor or
  patch version. Use when bumping, updating or upgrading a package, SDK,
  framework or GitHub Action; when reviewing a Dependabot or Renovate pull
  request; when a diff touches package.json, a lockfile, requirements.txt,
  pyproject.toml, go.mod, Cargo.toml, a Gradle version catalog, a .csproj or a
  workflow's `uses:` line; or when asked "is it safe to upgrade X", "what
  changed between 2.3 and 3.1", "what breaks if we move to Y" or "what do I
  need to change for this upgrade". Works for npm, PyPI, crates.io, RubyGems,
  Maven/Gradle, Go, NuGet and GitHub Actions.
license: MIT
compatibility: >-
  Uses the What's New MCP server (https://whatsnew.fyi/mcp, no key). Without
  it, needs python3 and network access to whatsnew.fyi.
---

# Upgrade review

Answer one question for each package being moved: **what has to change in this
codebase before the upgrade is safe to merge?** The vendor's release notes
already say what broke. The job is to find those notes across every release in
the range, quote the parts that matter, and check this codebase for each one.

The notes come from [What's New](https://whatsnew.fyi). It tracks the release
history of more than a thousand packages and apps, and its `upgrade_notes` tool returns
the vendor's own breaking-change, migration, deprecation and security sections
**verbatim**, for every tracked release between two versions.

## 1. Collect the moves

For each package, you need its name, the version installed now (`from`) and
the version it is moving to (`to`).

- **Versions come from the lockfile, not the manifest.** `^4.2.0` is a range.
  Read the resolved version from `package-lock.json`, `pnpm-lock.yaml`,
  `yarn.lock`, `poetry.lock`, `uv.lock`, `Cargo.lock` or `go.sum`, or from
  the diff's old and new lines. For a PR, `from` is the base branch's version.
- **Name each package the way its ecosystem does:** `@tanstack/react-query`,
  `django` with `registry: "pypi"`, `serde` with `registry: "crates"`, a Maven
  `group:artifact`, a Go module path, or an Action's `owner/repo@ref`.
  Maven, Go and NuGet packages can also go by purl
  (`pkg:maven/com.squareup.okhttp3/okhttp`, `pkg:nuget/Newtonsoft.Json`).
- **For npm, pass `repository`** from `node_modules/<name>/package.json`. It
  resolves scoped and renamed packages that the name alone cannot, and it makes
  the match exact.
- **Leave private packages out.** Workspace packages, anything from a private
  registry and internal forks can't be tracked, and their names shouldn't
  leave the machine. Omit them, and say you did.
- Omit `to` to get everything after `from` that is tracked. That's useful for
  "what am I missing" questions.

## 2. Call `upgrade_notes`

Send up to 20 dependencies per call. Split a larger upgrade into several calls.

```json
{"dependencies": [
  {"name": "better-auth", "from": "1.6.0", "to": "1.7.0",
   "repository": "github:better-auth/better-auth"}
]}
```

**If the What's New MCP tools are available** (their names end in
`upgrade_notes`, `missing_changes`, `whats_new`), call `upgrade_notes`
directly.

**If they aren't,** use the bundled script. It makes the same call over plain
HTTP and prints the same structured result:

```sh
python3 scripts/whatsnew_call.py upgrade_notes args.json
```

Exit 2 means the tool refused the input, and stderr says why. Fix the argument
and try again. Exit 1 is a network or protocol failure.

## 3. Read the result

Each dependency comes back with a `status`:

- **`ok`:** read `interval.releases` (how many tracked releases fall in the
  range), `signals` (`majorBump`, `breakingMentions`, `removed`, `deprecated`,
  `security`, `cves`), and `releases[]`.
- **`untracked`:** What's New doesn't carry this package. Say so. Don't
  describe the upgrade as safe, and don't fill the gap from memory. Point to
  the package's own changelog instead.
- **Any other status** (a range passed as a version, a version it can't
  place): read `notes`, fix the input if you can, and otherwise report it.

Always read `notes`. It explains how versions were matched, for example "1.6.0
is not a release we hold; the releases numbered up to it are", and what was
cut.

The substance is in `releases[].sections`. Each one has a `key` (`breaking`,
`migration`, `deprecated`, `security`), the vendor's `heading`, and the vendor's
`text` verbatim. In a monorepo release, `under` names the package the section
belongs to. Sections for other packages in the same release can be skipped when
this codebase doesn't use those packages.

`changes` is the categorized change list for the whole range, ordered
`removed`, `deprecated`, `security`, `changed`, `added`, `fixed`, with each
item tagged with its `versions`. When the list is capped, the later categories
are the ones cut. Vendors that don't write a "Breaking changes" heading still list
removals there, so read `removed` and `deprecated` as closely as the sections.

**When the result says it was cut** (`sectionsOmitted`, `truncated` or
`changesTruncated` is true), fetch `compareMarkdownUrl`. It's a plain GET that
returns the whole range as markdown, so read it before concluding that nothing
else breaks.

## 4. Check this codebase

This step is where the review earns its keep. For every breaking, removed,
renamed or deprecated item:

1. Pull out the concrete identifiers: function, option, import path, config
   key, CLI flag, environment variable.
2. Search the repository for each one. Include config files and tests, not
   just source.
3. Record each hit with its `file:line`, and whether the item affects this
   codebase at all.

A breaking change the codebase never touches isn't a blocker. It's still worth
one line in the report, so the reader knows it was checked.

## 5. Report

Lead with a verdict for each package, then the evidence:

```markdown
## better-auth 1.6.0 → 1.7.0 — merge after one change

14 tracked releases · 1 breaking section · 1 removal · no CVEs

**Blocking:** the MCP plugin moved to its own package (v1.7.0, breaking).
> Moved the MCP plugin into its own @better-auth/mcp package
- `src/lib/auth.ts:12` imports the MCP plugin from `better-auth`. Install
  `@better-auth/mcp` and import it from there.

**Checked, not affected:** … (one line each)

**Security fixes gained:** none in range.

Sources: [v1.7.0 on What's New](https://whatsnew.fyi/product/better-auth/releases/v1.7.0) ·
[vendor notes](https://github.com/better-auth/better-auth/releases/tag/v1.7.0) ·
[full range](https://whatsnew.fyi/product/better-auth/compare/1.6.0...v1.7.0)
```

Choose one of three verdicts:

- **Safe to merge:** no breaking item touches this code.
- **Merge after changes:** list each change with its `file:line`.
- **Hold:** the migration is large, the notes are ambiguous, or the package
  isn't tracked and the risk is unknown.

## Rules

- **Quote breaking and migration text; don't paraphrase it.** A summary
  softens exactly the detail that bites. Trim a long section to the relevant
  lines, but keep the vendor's words.
- **Never claim "no breaking changes" from silence.** Zero tracked releases, an
  `untracked` status or a cut result means "not known", not "none".
- **Cite every claim.** Link the release's What's New permalink (`url`) and the
  vendor's own notes (`sourceUrl`). The vendor's copy is the authoritative
  one. Credit What's New (whatsnew.fyi) once, as the source of the release
  history.
- **Keep provenance labels.** If an entry is marked as hand-curated or as
  having thin notes, keep that label.
- **Don't edit code or run installers unless asked.** This skill reviews. Offer
  to make the changes it found.
