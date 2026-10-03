# Distribution and releases

How the skills reach people, and what a release changes for them.

## Install paths

| Path | Command | What arrives |
| --- | --- | --- |
| Claude Code marketplace | `/plugin marketplace add whatsnew-fyi/skills`, then `/plugin install whatsnew@whatsnew-fyi` | every skill plus the MCP server |
| Any Agent Skills agent | `npx skills add whatsnew-fyi/skills` (`--skill <id>` for one) | the skill folders only, so the dependency skills fall back to `whatsnew_call.py` |
| MCP only | point a client at `https://whatsnew.fyi/mcp` (setup page: `https://whatsnew.fyi/mcp/setup`) | the tools with no skills |

The plugin's `.mcp.json` references the server by its `https://` URL rather than a
local process, so claude.ai and Cowork can offer it as a connector too.

## Public names

These names are typed by users, and changing any of them breaks existing installs
and docs (ADR 2026-09.d3hx):

- the marketplace name `whatsnew-fyi` and the plugin name `whatsnew`, which must
  match between the `marketplace.json` entry and `plugin.json`;
- the skill directory names, which become `/whatsnew:<id>`;
- the GitHub repository `whatsnew-fyi/skills`.

## Cutting a release

1. Bump `version` in `plugins/whatsnew/.claude-plugin/plugin.json`. Marketplace
   users get an update when the version changes, not on every commit.
2. Add the release to `CHANGELOG.md`. It is a Declarative Changelog, and CI validates
   it at Level 2 with zero warnings.
3. Bump the `USER_AGENT` version in every copy of `whatsnew_call.py`, so server logs
   can tell releases apart.
4. Run every check in `.agents/context/commands.md`, including the evals.
5. Tag `v<version>` and publish a GitHub release whose notes link the changelog
   entry.

## Directories worth listing in

Anthropic's plugin directory takes submissions (see
<https://claude.com/docs/directory/publish>). It takes the plugin folder,
`plugins/whatsnew/`, as its own submission, and shows `plugins/whatsnew/README.md` as
the listing's description. The root README doesn't count. The
[pre-submission checklist](https://claude.com/docs/plugins/pre-submission-checklist)
blocks a plugin folder without a README of at least 40 words outside code blocks,
and its security scan flags any destination the README doesn't disclose. So when a
skill starts running, sending or fetching something new, update that README's
"What the plugin runs, sends and fetches" section, and keep its links absolute. It
overlaps the root README on purpose: change both.

The portal's validator also checks these, and `claude plugin validate --strict` checks
none of them. Each came back as a warning on the first submission (2026-10-02):

- **Icon:** `plugins/whatsnew/.claude-plugin/icon.png` is the brand app icon, copied
  from `whatsnew-app`'s `public/icon-512.png` (the same artwork as the Play listing). It
  must be a square PNG or JPEG, 512 to 2048 px per side and under 2 MB. SVG and WebP
  are refused. ⚠ The portal reads it **only once**, at the plugin's first save or
  submit, so changing the file afterwards does not change the listing.
- **`privacyPolicyUrl`** in `plugin.json` points at `https://whatsnew.fyi/privacy`. Its
  `#mcp` section covers what the server keeps and what it sends on to deps.dev.
- **Reading a value from the user's machine** (an environment variable, a dotfile) is
  flagged with "ask through a `user_config` option instead". The only such read was an
  unused `WHATSNEW_MCP_URL` override in `whatsnew_call.py`, and it was deleted. A
  setting a skill really needs belongs in `userConfig`, with `sensitive: true` for a
  credential.
- **Name look-alikes:** `whatsnew` was held for review as too close to `whats-new`
  (`iskysun96/whats-new`). A hold is not a refusal. Renaming changes public names
  (ADR 2026-09.d3hx).

The reviewer then sent the first submission back for an unpinned launcher: the
`declarative-changelog` skill ran `npx -y declarative-changelog@0.2`, a range, and its
`compatibility` frontmatter named the package with no version at all. The review reads
skill text, not only hook and MCP commands. Every package a launcher runs is now an
exact version, and a test keeps it that way (see
[`skill-authoring.md`](../rules/skill-authoring.md)).

Skills directories such as
skills.sh index GitHub repositories that `npx skills` can read. The MCP server is
already listed in the official MCP registry as `fyi.whatsnew/changelogs`, and on
Smithery. Those listings belong to `whatsnew-app`, not to this repository.
