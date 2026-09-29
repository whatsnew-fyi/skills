---
type: llm
---

The workspace's CHANGELOG.md is Keep a Changelog style. 2.0.0 (2026-03-14) has a "BREAKING CHANGES" section with two items (the `--serial` flag removed; the config file renamed to `kestrel.config.mjs`), plus "Features" and "Bug Fixes" sections. The heading `1.9.0-beta.1 (beta) - 2026-02-02` carries a `(beta)` tag, and `[1.8.2] - 2026-1-20` has an unpadded date. The release links are reference-style definitions at the bottom of the file.

PASS only if the converted file in the final reply meets every one of these:

- It opens with YAML frontmatter containing `changelog: "0.1"` and a product name of Kestrel or kestrel.
- Every release heading puts its date last, as `2026-03-14`, `2026-02-02` and `2026-01-20` (1.8.2's date zero-padded).
- There is no `(beta)` tag in any heading. Keeping the `-beta.1` suffix and/or a `channel: beta` escape hatch is fine.
- There is no "BREAKING CHANGES" section. Both breaking items appear as list items opening with exactly `**Breaking**` followed by a separator, inside one of the six categories (Removed or Changed, for example).
- "Features" and "Bug Fixes" have become `### Added` and `### Fixed`.

FAIL if any heading gains a time of day or a date that the original file doesn't have, if a release or any item's wording is dropped, or if the reply claims the file was validated at a conformance level without having run the validator.
Ignore formatting outside the converted file, and ignore whether `## Unreleased` keeps its link.
