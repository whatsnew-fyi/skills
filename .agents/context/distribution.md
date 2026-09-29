# Distribution and releases

How the skills reach people, and what a release changes for them.

## Install paths

| Path | Command | What arrives |
| --- | --- | --- |
| Claude Code marketplace | `/plugin marketplace add whatsnew-fyi/skills`, then `/plugin install whatsnew@whatsnew-fyi` | both skills plus the MCP server |
| Any Agent Skills agent | `npx skills add whatsnew-fyi/skills` (`--skill <id>` for one) | the skill folders only, so the skill falls back to `whatsnew_call.py` |
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
<https://code.claude.com/docs/en/plugins/publish>). Skills directories such as
skills.sh index GitHub repositories that `npx skills` can read. The MCP server is
already listed in the official MCP registry as `fyi.whatsnew/changelogs`, and on
Smithery. Those listings belong to `whatsnew-app`, not to this repository.
