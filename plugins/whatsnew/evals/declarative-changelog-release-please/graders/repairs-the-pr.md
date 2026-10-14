---
type: llm
---

The workspace is a project whose `.github/workflows/release-please.yml` runs `googleapis/release-please-action` with no other steps, whose `release-please-config.json` uses the default changelog sections, and whose CI validates `CHANGELOG.md` with the `declarative-changelog` validator. release-please writes headings like `## [1.5.0](…) (2026-10-14)` and a `### ⚠ BREAKING CHANGES` section, which that validator rejects, and release-please has no setting that changes either.

PASS only if the reply proposes all of these:

- A step in the release-please workflow, after the action, that runs `declarative-changelog normalize --write` (or `normalize` with an equivalent write) on the release PR's branch and commits and pushes the result. Checking out the branch named by the action's `pr` output (`headBranchName`) is the expected way; any way that runs on the release PR's branch counts.
- Renaming release-please's changelog sections to the format's categories (at least Added and Fixed) in `release-please-config.json`.

FAIL if the reply relies on a release-please option that changes its heading or date format, tells the user to fix each release PR by hand, or weakens or removes the CI check.
Ignore the wording, and ignore extra suggestions that don't contradict these.
