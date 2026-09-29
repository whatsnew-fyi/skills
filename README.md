# What's New skills

Agent skills that read the release notes before you upgrade.

`upgrade-review` checks a dependency bump against the vendor's own breaking-change
and migration notes for every release in between, then finds the lines in your code
that the notes affect. `outdated-audit` turns `npm outdated` (or pip, Go, Cargo or
.NET's equivalent) into a ranked list of the security fixes and CVEs your project
doesn't have yet, split into the ones a plain update reaches and the ones that need
a version-range change.

Both get their data from [What's New](https://whatsnew.fyi), which tracks the release
history of more than a thousand packages, apps and tools and serves it over a public
[MCP server](https://whatsnew.fyi/mcp/setup). No API key, no sign-in.

## Install

**Claude Code:** add the marketplace, then install the plugin. It brings both skills
and connects the MCP server.

```text
/plugin marketplace add whatsnew-fyi/skills
/plugin install whatsnew@whatsnew-fyi
```

**Codex, Cursor, Gemini CLI and other Agent Skills agents:**

```sh
npx skills add whatsnew-fyi/skills
```

Installed this way, the skills reach the server through a small bundled script
(Python 3.8+ standard library, no dependencies). You can also point your agent's MCP
config at `https://whatsnew.fyi/mcp` so it calls the tools directly.

## Use

You don't need to name the skills. Ask the way you normally would:

- *"Dependabot wants to bump better-auth from 1.6.0 to 1.7.0. Can I just merge it?"*
- *"Review this Renovate PR."*
- *"What breaks if we move from Django 4.2 to 5.2?"*
- *"We're behind on dependencies. What should we update first?"*
- *"Are we missing any security fixes?"*

In Claude Code you can also run them directly: `/whatsnew:upgrade-review` and
`/whatsnew:outdated-audit`.

Here is what an upgrade review looks like, from an eval run against better-auth's
real 1.7.0 notes:

```markdown
**No, don't merge it as-is.** In better-auth 1.7.0 the minor-version bump includes a
long list of breaking changes, and `src/lib/auth.ts` uses several of them.

**Blocking 1: the MCP plugin has moved out of `better-auth`.**
> **Migration:** Install `@better-auth/mcp` and `@better-auth/cimd`, add the
> now-required `jwt()` plugin, … Rename `withMcpAuth` to `requireMcpAuth` …
- `src/lib/auth.ts:2` imports `mcp` and `withMcpAuth` from `better-auth/plugins`.
  That import needs to come from `@better-auth/mcp` instead.

**Blocking 2: the joins option has moved.**
> **Migration:** Replace `experimental: { joins: true }` with
> `advanced: { database: { joins: true } }`. …
- `src/lib/auth.ts:7` uses `experimental: { joins: true }`.
```

## What leaves your machine

The skills send `whatsnew.fyi` package names, version numbers and, for npm, each
package's public source-repository URL (which makes the match exact). They send no
source code, file paths or anything that names your project. Private packages stay
local.
The bundled converter drops npm workspace and private-registry packages, and takes
`--exclude '@yourorg/*'` for anything else internal.

When a Maven, Go or NuGet package isn't tracked yet, the server counts the miss per
day, with nothing about the caller, to decide what to track next. To turn that
off, ask your agent to pass `"recordMisses": false`.

## What the skills won't do

- **Change your code or run installers.** They review and audit. Updating is your
  call, and they give you the exact command.
- **Call an upgrade safe on missing data.** A package What's New doesn't track is
  reported as untracked, never as fine. For those, check the vendor's changelog.
- **Replace a vulnerability scanner.** The security counts come from what vendors
  wrote in their release notes. Pair the audit with `npm audit`, OSV or your
  scanner of choice.

## Contributing

This repository follows the [dotagents](https://github.com/bgreenwell/dotagents)
layout. [`AGENTS.md`](AGENTS.md) routes agents and people to the rules, context
and decisions under `.agents/`. The checks are in
[`.agents/context/commands.md`](.agents/context/commands.md).

Found a package What's New should track? Open an issue, or suggest it at
[whatsnew.fyi](https://whatsnew.fyi).

## License

[MIT](LICENSE)
