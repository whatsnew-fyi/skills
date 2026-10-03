# What's New

**Know what an upgrade changes before you merge it, and write release notes that tools read correctly.**

A Dependabot PR that bumps a minor version looks safe. Often it is. Sometimes the
vendor's notes for that release say a plugin moved to its own package, or a config
key was renamed, and you learn it from a failing deploy. This plugin reads those
notes for you, for every release in the range, and checks them against your code.

Release data comes from [What's New](https://whatsnew.fyi), which tracks the release
history of more than a thousand packages, apps and tools. The plugin connects its
public MCP server for you. No API key, no sign-in.

## The skills

### upgrade-review

*What has to change in this codebase before the upgrade is safe to merge?*

Collects the vendor's own breaking-change, migration, deprecation and security notes
for every release between your version and the target, quotes them verbatim, and
finds the lines in your code that each note affects. It flags breaking changes that
ship in minor and patch versions, which is where they are easiest to miss. Works for
npm, PyPI, crates.io, RubyGems, Maven/Gradle, Go, NuGet and GitHub Actions.

### outdated-audit

*What is this project missing by being behind, and what should we update first?*

Turns your package manager's outdated report into a ranked list of the security
fixes, CVEs and bug fixes your project doesn't have yet. It separates what a plain
update reaches inside your declared version ranges from what needs a manifest
change, and puts the cost of each move beside it: major bumps, breaking changes,
removals. Reads reports from npm, pnpm, yarn 1, pip, uv, Go, Cargo and .NET.

### declarative-changelog

*Does our changelog say what changed, in a form both a reader and a parser get right?*

Converts your `CHANGELOG.md` to the [Declarative Changelogs](https://whatsnew.fyi/spec)
format: Keep a Changelog plus YAML frontmatter, a strict release-heading grammar and
an exact `**Breaking**` marker, so bots and aggregators stop guessing at your
versions, dates and breaking changes. It drafts new entries from your Conventional
Commits, rewrites them for readers, writes the one-sentence summary (or asks you when
the commits don't make the point of a release clear), and runs the validator until
the file is clean. This skill works locally and calls no server.

## Use

You don't need to name the skills. Ask the way you normally would:

- *"Dependabot wants to bump better-auth from 1.6.0 to 1.7.0. Can I just merge it?"*
- *"What breaks if we move from Django 4.2 to 5.2?"*
- *"We're behind on dependencies. What should we update first?"*
- *"Are we missing any security fixes?"*
- *"Add the 2.0.0 release to CHANGELOG.md from the commits since v1.4.0."*
- *"Convert our CHANGELOG.md to a declarative changelog."*

In Claude Code you can also run `/whatsnew:upgrade-review`,
`/whatsnew:outdated-audit` or `/whatsnew:declarative-changelog` directly.

## Example

An upgrade review from an eval run against better-auth's real 1.7.0 release notes:

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

## Install

In Claude Code, add the marketplace and install the plugin. It brings all three
skills and connects the MCP server.

```text
/plugin marketplace add whatsnew-fyi/skills
/plugin install whatsnew@whatsnew-fyi
```

For Codex, Cursor, Gemini CLI and other Agent Skills agents, see the
[repository README](https://github.com/whatsnew-fyi/skills#install).

## What each skill needs

- **upgrade-review** and **outdated-audit** use the What's New MCP server that the
  plugin connects. Where MCP isn't available, a bundled script makes the same call
  over HTTPS, which needs `python3` (3.8+, standard library only) and network access
  to whatsnew.fyi. **outdated-audit** also runs a bundled `python3` converter, and
  reads the report from your package manager (Cargo needs `cargo-outdated`). You
  can paste the report instead.
- **declarative-changelog** needs `git` and `python3` to draft entries, and Node.js
  20 or later to run the validator, which `npx` fetches from npm. Without Node it
  applies the format by hand and tells you the file wasn't validated.

## What the plugin runs, sends and fetches

The plugin's own network traffic goes to two places: **whatsnew.fyi**, for release
data, and the **npm registry**, to fetch the changelog validator.

**Sent to whatsnew.fyi** by `upgrade-review` and `outdated-audit`, through the MCP
server at `https://whatsnew.fyi/mcp` or the fallback script:

- package names, their registry, and version numbers: installed, newest in range,
  and newest published;
- for npm packages, each package's public source-repository URL, and for Go and
  NuGet packages, a package URL (purl). Both make the match exact.

They send no source code, file paths or anything that names your project. Requests
from the fallback script carry a User-Agent that names the plugin's version.

**Private packages stay on your machine.** The converter leaves out npm workspace
packages and packages from private registries on its own. For anything else
internal, in any ecosystem, it takes `--exclude '@yourorg/*'`, and the agent leaves
out the packages you name as internal.

**Untracked packages help decide what to track next.** When a Maven, Go or NuGet
package isn't tracked yet, the server checks the name against deps.dev and counts
the miss per day, with nothing about the caller. To turn that off, ask your agent to
pass `"recordMisses": false`.

**Fetched:**

- a whatsnew.fyi compare page, as markdown, when an upgrade review's result was cut
  short;
- the `declarative-changelog` validator from npm, run with
  `npx -y declarative-changelog@0.2.0`.

**Run on your machine:**

- your package manager's outdated command, such as `npm outdated --json`, unless you
  paste the report;
- `outdated_to_deps.py`, which reads that report and, for npm, each package's
  installed `package.json`;
- `whatsnew_call.py`, only when the MCP server isn't available;
- `draft_entry.py`, which runs a read-only `git log` and prints a draft without
  writing any file;
- `declarative-changelog validate`.

**Written:** only the `CHANGELOG.md` you ask `declarative-changelog` to write.

## What the skills won't do

- **Change your code or run installers.** They review and audit. Updating is your
  call, and they give you the exact command.
- **Invent release facts.** `declarative-changelog` leaves out a date, version or
  link it can't find in your repository, and tells you which ones.
- **Call an upgrade safe on missing data.** A package What's New doesn't track is
  reported as untracked, never as fine. For those, check the vendor's changelog.
- **Replace a vulnerability scanner.** The security counts come from what vendors
  wrote in their release notes. Pair the audit with `npm audit`, OSV or your
  scanner of choice.

## Links

- Source and issues: [github.com/whatsnew-fyi/skills](https://github.com/whatsnew-fyi/skills)
- MCP server setup for other clients: [whatsnew.fyi/mcp/setup](https://whatsnew.fyi/mcp/setup)
- The Declarative Changelogs spec: [whatsnew.fyi/spec](https://whatsnew.fyi/spec)
- Suggest a package to track: [whatsnew.fyi/suggest](https://whatsnew.fyi/suggest)

## License

[MIT](https://github.com/whatsnew-fyi/skills/blob/main/LICENSE)
