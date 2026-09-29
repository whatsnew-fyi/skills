---
type: llm
---

The workspace's CHANGELOG.md is a declarative changelog with `versioning: semver`, whose newest release is 1.4.0 under an empty `## Unreleased`. The commits are a feature (`--json`, #212), a fix (empty config crash, #207), a breaking `feat!` dropping Node 18, and a dependency-bump chore.

PASS only if the entry in the final reply meets every one of these:

- Its heading is a `## ` heading for version 2.0.0 (a `v` prefix is fine), with the date `2026-09-28` (optionally with a time) last, for example `## [2.0.0](…) — 2026-09-28`.
- It has a summary blockquote (`> …`) of real prose directly under the heading, not a TODO placeholder.
- The Node 18 change is a list item opening with exactly `**Breaking**` and a separator, under one of the six categories.
- The `--json` item is under `### Added`, and the empty-config crash is under `### Fixed`.
- No item mentions the yaml dependency bump.
- The reply places the entry above 1.4.0 (below `## Unreleased`, if it mentions it).

FAIL if the version is not 2.0.0, if 1.4.0's entry is changed, or if the reply claims the result was validated without having run the validator.
Ignore the wording of the items, as long as each commit's meaning survives.
