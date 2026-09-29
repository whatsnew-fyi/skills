# Declarative Changelogs v0.1: the rules that bite

This is a working summary of the [Declarative Changelogs](https://whatsnew.fyi/spec)
standard, **v0.1 (a provisional draft)**, and of the rule ids the
`declarative-changelog` validator reports. The full text, which wins wherever this
summary is silent, is served as Markdown at <https://whatsnew.fyi/spec.md>.

A declarative changelog is an ordinary `CHANGELOG.md`: YAML frontmatter, one `# `
title, then one `## ` heading per release, **newest first**. Every fact a tool would
otherwise guess, the publisher states.

## Minimal document

````markdown
---
changelog: "0.1"
product:
  name: Kestrel
  vendor: Corvid Labs
  homepage: https://kestrel.example
  versioning: semver
document:
  updated: 2026-07-28T14:02:00Z
  coverage: complete
---

# Kestrel changelog

## Unreleased

## [2.4.0](https://kestrel.example/releases/2.4.0) — 2026-07-09T14:00:00Z

> Task graphs run in parallel by default, cutting cold builds roughly in half.

### Added

- Tasks with no declared dependency on each other now run in parallel. (#1204)

### Removed

- **Breaking** — the `--serial` flag has been removed; use `--jobs 1`.
````

## YAML profile

Both YAML blocks (the frontmatter and the escape hatch) are read as maps, sequences and
strings only. `1.10` stays the string `1.10`. **No anchors, aliases, custom tags,
directives or `---` multi-document streams.** A boolean is exactly `true` or `false`.

## Frontmatter

Only `changelog` is required. Unknown keys under `product.` or `document.` are
**errors**; unknown top-level keys only warn. Keys starting `x-` are allowed anywhere.

| Key | Value |
| --- | --- |
| `changelog` | `"0.1"` (quote it) |
| `product.name` | display name; without it the document can't be attributed |
| `product.vendor` | who publishes it |
| `product.homepage` | URL of the product, not of the changelog |
| `product.id` | stable id; defaults to `name` slugged. Explicit ids match `[a-z0-9][a-z0-9-]*` |
| `product.description` | one line |
| `product.platforms` | list from: `windows`, `macos`, `linux`, `ios`, `android`, `web`, `playstation`, `xbox`, `switch` |
| `product.versioning` | `semver`, `calver` or `none`. Only `semver` turns on the version/content check. State it only when it is true |
| `product.category` | any string, advisory |
| `product.color` | six hex digits, **bare**: `color: 1a73e8`. `color: #1a73e8` is an empty value, because `#` starts a YAML comment |
| `document.updated` | RFC 3339 timestamp of the last edit |
| `document.coverage` | `complete` or `partial`. Absent means unknown, so omit it rather than guess |
| `document.canonical` | URL where people read this changelog |
| `document.locale` | BCP 47 tag, default `en` |
| `document.older` | URL of the next-older document; **required** with `coverage: partial` |

## Release heading

```text
release-heading := "## " (label-part sep)? date tags?
label-part      := "[" label "](" url ")" | label
label           := version | version ": " title | title
version         := "v"? DIGIT+ ("." DIGIT+)+ ("-" pre)? ("+" build)?
sep             := " — " | " – " | " - "
date            := RFC 3339 full-date ("T" partial-time time-offset)?
tags            := " (" tag (", " tag)* ")"
```

All of these are conformant:

```markdown
## [2.4.0](https://kestrel.example/releases/2.4.0) — 2026-07-09T14:00:00Z
## 2.4.0 — 2026-07-09
## v2.5.0-rc.1: Parallel graphs — 2026-07-01
## Parallel task graphs — 2026-07-09
## 2026-07-09
```

- **The date comes last** (before any tags), zero-padded, `YYYY-MM-DD`. A time needs
  `T` and an offset (`Z` or `+02:00`). A date-only value means midnight UTC.
- **Any `## ` heading containing `YYYY-MM-DD` is a release candidate**, and must parse.
  `## Release notes for 2026-05-02` is an error. `## Unreleased` and other dateless
  headings are skipped at no cost.
- **Pre-releases use the semver suffix** (`2.5.0-rc.1`). PEP 440's `1.0rc1` is read as
  a title, so write `1.0.0-rc.1`. A channel name as a suffix (`-stable`, `-lts`) warns;
  channels go in the escape hatch.
- **Tags are closed:** `yanked` (don't use this release; the notes stay) and `routine`
  (nothing a reader needs to read). There are no channel or platform tags: `(beta)`,
  `(lts)` and `(linux)` are errors.

## Entry body

- **Summary:** the blockquote directly after the heading (or after its hatch). One
  paragraph of plain prose. A `> [!NOTE]` alert never counts. This is the most valuable
  optional line, and no generator can write it.
- **Change sections:** `### Added`, `### Changed`, `### Deprecated`, `### Removed`,
  `### Fixed`, `### Security`, in that order. Each holds **a list and nothing else**.
  The same category twice in one entry is an error. Other `###` headings are legal but
  cap the document at Level 1.
- **Change item:** one top-level list item per change. Its first paragraph is the
  change; later paragraphs and nested lists are detail.
- **Reference tail:** a trailing `(#123)`, `(GH-1204)`, a CVE id, a link, or
  `thanks to @handle` is detached into a structured reference. Keep references at the
  end of the item.
- **Breaking:** open the item with exactly `**Breaking**` plus a separator
  (`**Breaking** — …`), inside the category the change belongs to. `**BREAKING**`,
  `**Breaking:**` and `**Breaking change**` are near-misses.
- **Routine:** a `(routine)` entry has no change sections.
- **Content, not a pointer:** an entry whose whole body is a link to notes elsewhere
  fails Level 1.
- **No raw HTML.** Images need alt text and must not carry the meaning alone.

### Version and content agree (only with `versioning: semver`)

| An entry containing | should be at least |
| --- | --- |
| a `**Breaking**` item | a major bump |
| `### Added` items | a minor bump |
| only `### Fixed` items | a patch bump |

0.x releases and pre-release finalizations are exempt.

## Escape hatch

A fenced block with info string `changelog`, **immediately after the `## ` heading and
before the summary**. It uses the YAML profile. Where it and the heading disagree, the
hatch wins, and the validator warns. Use it only for what the heading cannot say.

````markdown
## [1.129](https://code.example/updates/v1_129) — 2026-06-11

```changelog
covers: ["1.129.1", "1.129.2"]
```

> Faster search, and two patch releases folded in.
````

| Key | For |
| --- | --- |
| `channel` | release channel: `lts`, `beta`, `insiders`, `nightly`, … |
| `url` | the entry's permalink, when the heading has no link |
| `prerelease` | `true` **only** on a versionless entry (an error on a versioned one) |
| `platforms` | the entry's platforms, where they differ from the product's |
| `covers` | other versions documented here with no entry of their own. Items may open `- **1.129.1** — …`, naming one of them |
| `superseded-by` | the release to move to. Must resolve. A `yanked` entry should have one |
| `id` | explicit stable id (two versionless releases on one day) |
| `version`, `title`, `date` | overrides for a heading that is wrong and can't be fixed |

## Identity and ordering

- An entry's id is the hatch `id`, else `<product.id>@<version>` (without `v`), else
  `<product.id>@<YYYY-MM-DD>`.
- Ids must be unique and **stable across edits**. Never change a published entry's
  version or date, and never add a hatch `id` to an entry that didn't have one.
  Adding `(yanked)` doesn't change the id.
- Entries run newest first, including entries on the same date.

## Conformance

- **Level 1, Structured:** the frontmatter parses, every candidate heading parses,
  ids are unique, entries are newest first, and no body is only a link.
- **Level 2, Categorized:** Level 1, plus every top-level list sits under one of the
  six `###` categories.
- **Addressable** (reported, not a level): every entry has its own URL, from the
  heading link or the hatch `url:`.

## From Conventional Commits

| Commit type | Category |
| --- | --- |
| `feat` | Added |
| `fix` | Fixed |
| `perf`, `revert` | Changed |
| `security` (extension) | Security |
| `deprecate` (extension) | Deprecated |
| `remove` (extension) | Removed |
| `docs`, `style`, `refactor`, `test`, `build`, `ci`, `chore` | none; a release of only these is `routine` |

`!` or a `BREAKING CHANGE:` footer adds the `**Breaking** — ` marker.
`scripts/draft_entry.py` applies this table. Commit subjects describe the work, not
the change a reader sees, so rewrite them.

## Validator rule → fix

`npx -y declarative-changelog@0.2 validate CHANGELOG.md --format json` reports each
problem with a `rule` id and a position.

| Rule | Fix |
| --- | --- |
| `frontmatter/missing`, `frontmatter/changelog-required` | add the `---` block with `changelog: "0.1"` |
| `frontmatter/profile` | remove anchors (`&`), aliases (`*`), `!!tags` and extra `---` documents |
| `frontmatter/unknown-key` | a typo, or a key the spec doesn't have. Rename it to `x-…` to keep it |
| `frontmatter/invalid-color` | write the hex bare: `color: 1a73e8` |
| `frontmatter/older-required` | add `document.older`, or drop `coverage: partial` |
| `heading/candidate-does-not-parse` | fix to the grammar: pad the date, put it last, use ` — `, replace a no-break space. If it isn't a release, take the date out of the heading |
| `heading/unknown-tag` | only `yanked` or `routine`. Move a channel to the hatch `channel:` and a platform to `platforms:` |
| `heading/channel-as-prerelease` | `2.0.0-stable` is a pre-release named `stable`: drop the suffix, and put the channel in the hatch |
| `order/not-newest-first` | reorder the entries, newest first |
| `identity/duplicate-id` | two entries share a version or a versionless date: give one a hatch `id` |
| `hatch/misplaced` | move the ```` ```changelog ```` block directly under its `##` heading, before the summary |
| `hatch/prerelease-with-version` | remove `prerelease:`; the version's `-rc.1` suffix already says it |
| `entry/section-content` | a category section may hold only a list: move prose to the summary or into an item |
| `entry/duplicate-section` | merge the two sections |
| `entry/routine-with-changes` | drop `(routine)`, or drop the sections |
| `entry/link-only-body` | write the notes in the entry; keep the link in the heading |
| `entry/breaking-near-miss` | exactly `**Breaking** — ` |
| `entry/section-order` | Added, Changed, Deprecated, Removed, Fixed, Security |
| `conformance/uncategorized-sections` | map `### Features` → Added, `### Bug Fixes` → Fixed, `### Performance` → Changed. Custom sections keep the document at Level 1 |
| `relation/yanked-without-superseded-by` | add `superseded-by:` to the yanked entry's hatch |
| `relation/superseded-by-unresolved` | point it at a version this document has, or covers |
| `semver/breaking-needs-major`, `semver/added-needs-minor` | a real mismatch: fix the notes if they're wrong. Never renumber a published release; say so instead |
| `heading/date-only` (info) | add a time and offset when you know it (`git log -1 --format=%aI <tag>`) |
| `media/raw-html` | replace the HTML with Markdown |
