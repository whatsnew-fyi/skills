---
id: "2026-09.wez2"
slug: private-packages-never-leave-the
title: "private packages never leave the machine, and misses stay recorded"
date: 2026-09-28
topics: [privacy, mcp]
---

# ADR 2026-09.wez2 — private packages never leave the machine, and misses stay recorded

Status: Accepted (2026-09-28)

**Context:** both tools take package names, and `recordMisses` (default true) makes the
server check an untracked Maven, Go or NuGet package against deps.dev and count it per
day, with nothing about the caller. The count is how What's New decides what to track
next. A project's outdated report also lists workspace packages, private-registry
packages and internal forks. On the first end-to-end run (2026-09-28), a monorepo's
`npm outdated` listed its own `@whatsnew/core` workspace package, and it went to the
server.

**Decision:** private packages are left out of the call instead of being sent with
`recordMisses: false`. The server can never track them, so sending them buys nothing
and leaks an internal name. `outdated_to_deps.py` drops npm packages whose installed
`package.json` says `"private": true` or whose `publishConfig.registry` is not
npmjs.org, takes `--exclude` globs for everything else, and reports every skip on
stderr. The skills tell the agent to do the same by hand, and to tell the user what
was left out. Public packages keep the server's default `recordMisses: true`, because
that demand signal is what grows the catalog the skills depend on.

**Consequences / limits:** the npm check needs `node_modules` present. Without it, only
`--exclude` protects a private package. Private packages in other ecosystems are not
detected at all, so the skill text asking the agent to exclude them is the guard.
`tests/test_scripts.py` covers the npm private and publishConfig cases.
