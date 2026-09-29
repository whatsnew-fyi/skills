#!/usr/bin/env bash
# A declarative changelog one release behind.
set -euo pipefail
cat > package.json <<'JSON'
{ "name": "kestrel", "version": "1.4.0", "homepage": "https://kestrel.example" }
JSON
cat > CHANGELOG.md <<'MD'
---
changelog: "0.1"
product:
  name: Kestrel
  homepage: https://kestrel.example
  versioning: semver
document:
  updated: 2026-08-01T10:00:00Z
  coverage: complete
---

# Kestrel changelog

## Unreleased

## [1.4.0](https://github.com/corvid/kestrel/releases/tag/v1.4.0) — 2026-08-01T10:00:00Z

> Remote cache backends for any S3-compatible bucket.

### Added

- Task outputs can be pushed to any S3-compatible bucket.

### Fixed

- The scheduler no longer stalls on cyclic `dependsOn` graphs.
MD
