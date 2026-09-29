---
name: declarative-changelog
description: >-
  Write, convert and validate a CHANGELOG.md in the Declarative Changelogs
  format: Keep a Changelog plus YAML frontmatter, a strict release-heading
  grammar and an exact Breaking marker, so aggregators, bots and agents read
  every release without guessing. Drafts entries from Conventional Commits and
  checks the file with the declarative-changelog validator. Use when adding a
  release entry to CHANGELOG.md, writing a changelog or release notes from
  commits, preparing or cutting a release, converting an existing changelog or
  Keep a Changelog file, fixing `declarative-changelog validate` errors, adding
  a changelog check to CI or a pre-commit hook, or when a CHANGELOG.md starts
  with `changelog: "0.1"` frontmatter.
license: MIT
compatibility: >-
  Validates with `npx declarative-changelog` (Node.js 20+, fetched from npm).
  The draft script needs python3 and git. Calls no other service.
---

# Declarative changelog

Answer one question about the project's changelog: **does it say what changed, in a
form that both a reader and a parser get right?** A declarative changelog still
reads like an ordinary `CHANGELOG.md`, but every fact a tool would otherwise guess
is stated: the version, the date, the category of each change, what breaks, which
releases are routine. The format is the
[Declarative Changelogs](https://whatsnew.fyi/spec) standard (v0.1, a draft), and
`declarative-changelog` on npm is its reference validator.

The rules that matter while editing are in
[`references/format.md`](references/format.md). Read it before writing a heading
or frontmatter.

## 1. Find the job

Locate the changelog (`CHANGELOG.md`, sometimes `CHANGES.md` or `HISTORY.md`), and
work out which of these the user wants:

- **Adopt:** there is no changelog, or it isn't in the format yet. Go to step 3.
- **Add a release:** the file is already declarative (its frontmatter has
  `changelog: "0.1"`). Go to step 4.
- **Fix diagnostics:** the validator or CI failed. Go to step 5.
- **Gate CI:** go to step 6.

## 2. Validate first

```sh
npx -y declarative-changelog@0.2 validate CHANGELOG.md --format json
```

Read `files[0].level` (0, 1 or 2), `entries`, `skipped`, and each diagnostic's
`rule`, `severity`, `message` and `position.line`. Exit 0 means valid, 1 means it
found problems, and 2 is a usage error. For a quick human view, drop `--format json`.

**If Node isn't available,** say that the file wasn't validated, and apply
`references/format.md` by hand. Don't report a conformance level you didn't
measure.

## 3. Adopt the format

Restructure the file. **Keep the existing notes word for word.** Only headings,
section names and placement change.

1. **Frontmatter.** State only facts the repository states. Take `product.name`,
   `homepage` and `description` from `package.json`, `pyproject.toml`,
   `Cargo.toml` or the README. Set `versioning: semver` only when the tags are
   semver. Set `coverage: complete` only when every release is in the file;
   otherwise leave it out. Set `document.updated` to now, in RFC 3339.
2. **Headings.** Rewrite each release to
   `## [1.4.0](<release url>) — 2025-11-03T09:12:44Z`. Keep the version exactly as
   published. Use a link only if one exists: a GitHub release, a tag page, or the
   project's own release page.
3. **Dates.** Take missing or partial dates from the tag:
   `git log -1 --format=%aI v1.4.0`. **Never invent a date.** A release with no
   knowable date keeps a dateless heading, so it is skipped rather than
   misdated. List those in the report.
4. **Sections.** Map them to the six categories: Features or New → `Added`, Bug
   Fixes → `Fixed`, Performance or Improvements → `Changed`, Security → `Security`.
   A "Breaking changes" section is dissolved: each item moves into the category it
   belongs to (usually `Changed` or `Removed`) and opens with `**Breaking** — `.
   Prose under a category heading becomes the summary blockquote or an item.
5. **Tags and channels.** `(beta)` or `[LTS]` in a heading become a semver
   pre-release suffix or a hatch `channel:`. A withdrawn release gets `(yanked)` and
   a `superseded-by:`.
6. Keep `## Unreleased` at the top. It is skipped by design.

## 4. Add a release

Draft the entry from the commits since the last tag:

```sh
python3 scripts/draft_entry.py --since v1.4.0 \
  --url 'https://github.com/OWNER/REPO/releases/tag/v{version}'
```

It prints the entry to stdout. On stderr it reports the suggested semver bump,
which types it hid (`chore`, `ci`, `docs`, …), and every commit it couldn't
classify. It never writes files. Pass `--version` to set the version yourself.
Without it, the draft takes the suggested bump from `--previous` (or from
`--since`, if that is a version).

Then turn the draft into notes:

- **Rewrite each item for a reader.** A commit subject describes the work
  ("refactor(parser): extract heading scan"). An item says what changed for the
  person using the product. Merge commits that are one change, and drop ones a
  reader wouldn't notice. Keep issue and PR references at the end of the item.
- **Read the unclassified commits.** A non-conventional subject may still be a
  user-facing change. Place it by hand, or leave it out and say so.
- **Write the summary.** One sentence on what the release means for someone using
  it. The script leaves a `TODO` there because generation can't do this. If the
  point of the release isn't clear from the commits, ask.
- **Fold in `## Unreleased`.** Move its items into the new entry, and leave the
  heading empty.
- **Place it newest first,** directly under `## Unreleased`, and update
  `document.updated`.
- **Don't touch published entries.** Their version and date make their id, and a
  changed id is re-delivered to every reader as a new release.

## 5. Validate until clean

The target is Level 2 with no warnings:

```sh
npx -y declarative-changelog@0.2 validate CHANGELOG.md --require-level 2 --max-warnings 0
```

Fix each diagnostic with the "Validator rule → fix" table in
`references/format.md`, and re-run. Some things need a human, not a fix: a
`semver/*` warning on a published release, or a date that can't be recovered.
Report those, quoting the validator's message.

## 6. Offer the gate

Offer to add the same check to CI so the file stays valid. Don't add it unasked.

```yaml
# .github/workflows/ci.yml
- run: npx -y declarative-changelog@0.2 validate CHANGELOG.md --require-level 2 --max-warnings 0
```

For an npm project, a `"changelog:check"` script with the same command works in CI
and in a pre-commit hook.

## Report

End with what changed and where the file stands:

```markdown
**CHANGELOG.md is now a Level 2 declarative changelog** (12 entries, 12 addressable, 0 warnings).

- Added frontmatter: name, homepage and `versioning: semver` from package.json. `coverage` is left out, because releases before 1.0 aren't in the file.
- Rewrote 12 headings; took 4 dates from their tags.
- Dissolved "Breaking changes" in 2.0.0 into 3 `**Breaking**` items under Changed and Removed.
- **Needs you:** 0.9.0 has no tag or date, so it stays a dateless heading and is skipped.
```

## Rules

- **Absent beats guessed.** No invented dates, versions, URLs or coverage. Leave the
  field out, and say you did.
- **The notes are the publisher's words.** While converting, restructure and never
  paraphrase. While adding a release, rewrite commit subjects into notes, because a
  commit message was never a note.
- **The Breaking marker is exact:** `**Breaking** — `, inside the category the
  change belongs to.
- **Use the escape hatch only for what the heading can't say:** a channel, a
  per-entry platform set, covered versions, `superseded-by`.
- **Keep custom metadata under `x-` keys**, and write `product.color` as bare hex.
- **Edit only the changelog.** Don't change versions, tags or manifests to satisfy a
  `semver/*` warning. Report the mismatch.
- **Never claim a conformance level you didn't measure.** Quote the validator's
  result.
