#!/usr/bin/env bash
# A declarative changelog that release-please writes to, and a CI check it fails.
set -euo pipefail
mkdir -p .github/workflows
cat > package.json <<'JSON'
{ "name": "kestrel", "version": "1.4.0", "repository": "github:corvid/kestrel" }
JSON
cat > release-please-config.json <<'JSON'
{
  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
  "packages": {
    ".": { "release-type": "node" }
  }
}
JSON
cat > .release-please-manifest.json <<'JSON'
{ ".": "1.4.0" }
JSON
cat > .github/workflows/release-please.yml <<'YAML'
name: Release Please
on:
  push:
    branches: [main]
permissions:
  contents: write
  pull-requests: write
jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v5
YAML
cat > .github/workflows/ci.yml <<'YAML'
name: CI
on: [push, pull_request]
jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - run: npx -y declarative-changelog@0.4.0 validate CHANGELOG.md --require-level 2 --max-warnings 0
YAML
cat > CHANGELOG.md <<'MD'
---
changelog: "0.1"
product:
  name: Kestrel
  homepage: https://github.com/corvid/kestrel
  versioning: semver
document:
  updated: 2026-08-01T10:00:00Z
---

# Kestrel changelog

## [1.4.0](https://github.com/corvid/kestrel/compare/v1.3.0...v1.4.0) - 2026-08-01

### Added

- Task outputs can be pushed to any S3-compatible bucket.
MD
