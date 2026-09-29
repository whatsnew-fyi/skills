# The What's New MCP server, as the skills use it

Reference for anything a skill sends to the server or reads back. The server
itself lives in the private `whatsnew-app` repository. A skill change that needs
a server change goes there first, and the skill ships after production serves it.

## The door

- `POST https://whatsnew.fyi/mcp`, streamable HTTP, no key and no sign-in.
- **Stateless.** A bare `tools/call` answers without `initialize` or a session id.
  That is what lets `whatsnew_call.py` be one request.
- Replies are SSE-framed (`event: message` / `data: {...}`) for clients that accept
  `text/event-stream`. That's spec-standard streamable HTTP, not a bug.
- Every result carries the payload twice: as a JSON string in `content[0].text`, and
  as `structuredContent`. Read `structuredContent`.
- A domain miss (an unknown product, bad input) comes back as `isError: true` with a
  readable message. It is not a JSON-RPC error.
- Rate limited per IP at the edge. A burst of calls from one machine can see 429s.

## The tools the skills call

| Tool | Skill | Per call | Required input |
| --- | --- | --- | --- |
| `upgrade_notes` | `upgrade-review` | 20 deps | `name`, `from`; `to` optional |
| `missing_changes` | `outdated-audit` | 100 deps | `name`, `from`; `wanted`, `latest` optional |
| `whats_new` | none yet | 1 product | `product`; `since_version` optional |
| `list_products`, `search_releases` | none yet | | |

Both dependency tools also take `purl`, `registry` (`npm` by default, or `pypi`,
`crates`, `rubygems`), `repository` (which makes the match exact for scoped and
renamed packages), and a top-level `recordMisses`.

## What comes back

- **`status`** for each dependency. `upgrade_notes`: `ok`, `untracked`, `unreadable`
  (a range was passed as a version), and a few that say why a pair has no interval.
  `missing_changes`: `ok` or `untracked`. `notes[]` explains how versions were
  matched and what was cut.
- **`upgrade_notes`** returns `interval` (`releases`, `oldest`, `newest`), `signals`
  (`majorBump`, `breakingMentions`, `removed`, `deprecated`, `security`, `cves`),
  `changes[]` by category (ordered removed, deprecated, security, changed, added,
  fixed, so a cap cuts the harmless end), and `releases[]`. Each release has `url`
  (What's New permalink), `sourceUrl` (the vendor's notes) and `sections[]`
  (`key` ∈ breaking/security/deprecated/migration, the vendor `heading`, `under` for
  monorepo packages, and `text` verbatim).
- **Caps:** sections are cut at 8,000 characters per release, 16,000 per dependency
  and 48,000 per call. When anything is cut, `compareMarkdownUrl` serves the whole
  range as markdown on a plain GET.
- **`missing_changes`** returns `summary` (`tracked`, `behindInRange`,
  `withSecurity`, `cves`), and per package the `toWanted` and `toLatest` blocks,
  each with `gain` (`security`, `fixed`, `cves`), `cost` (`majorBump`,
  `breakingMentions`, `removed`, `deprecated`), a few `items`, and `compareUrl`.

The authoritative shapes are the output schemas in
`plugins/whatsnew/evals/mocks/whatsnew/_tools.json`, recorded from production.

## recordMisses

When `recordMisses` is true (the default), a Maven, Go or NuGet package the server
doesn't track is checked against deps.dev after the answer, and counted per day with
nothing about the caller. The count decides what gets tracked next. The skills keep
the default for public packages and leave private ones out of the call entirely
(ADR 2026-09.wez2).
