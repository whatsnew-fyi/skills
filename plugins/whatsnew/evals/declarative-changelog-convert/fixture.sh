#!/usr/bin/env bash
# A Keep a Changelog-style file with the near-misses a conversion has to fix.
set -euo pipefail
cat > package.json <<'JSON'
{
  "name": "kestrel",
  "version": "2.0.0",
  "description": "A task runner with a parallel build graph.",
  "homepage": "https://kestrel.example",
  "repository": "github:corvid/kestrel"
}
JSON
cat > CHANGELOG.md <<'MD'
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Features

- Watch mode for `kestrel test`.

## [2.0.0] - 2026-03-14

### BREAKING CHANGES

- The `--serial` flag has been removed; use `--jobs 1`.
- The config file is now `kestrel.config.mjs`; `kestrel.config.js` is no longer read.

### Features

- Task graphs run in parallel by default.

### Bug Fixes

- `kestrel watch` no longer misses edits to symlinked files.

## 1.9.0-beta.1 (beta) - 2026-02-02

### Features

- Experimental remote cache.

## [1.8.2] - 2026-1-20

### Bug Fixes

- Fix crash when the config file is empty.

[Unreleased]: https://github.com/corvid/kestrel/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/corvid/kestrel/releases/tag/v2.0.0
[1.8.2]: https://github.com/corvid/kestrel/releases/tag/v1.8.2
MD
