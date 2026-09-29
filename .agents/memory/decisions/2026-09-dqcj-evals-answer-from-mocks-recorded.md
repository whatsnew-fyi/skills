---
id: "2026-09.dqcj"
slug: evals-answer-from-mocks-recorded
title: "evals answer from mocks recorded off production"
date: 2026-09-28
topics: [evals, testing]
---

# ADR 2026-09.dqcj — evals answer from mocks recorded off production

Status: Accepted (2026-09-28)

**Context:** `claude plugin eval` never starts a plugin's real MCP servers unless asked,
and a real server would make scores move whenever the catalog does. Hand-written mock
answers would drift from the real output schema without anyone noticing, and the
skills' instructions name real fields (`sectionsOmitted`, `toWanted`,
`compareMarkdownUrl`).

**Decision:** the suite-wide mocks under `plugins/whatsnew/evals/mocks/whatsnew/` answer
from `fixtures/*.json`, which are `structuredContent` bodies recorded from production on
2026-09-28. `_tools.json` is the production `tools/list`, so mocked tools carry their
real descriptions and schemas. Each case grades three things: that the skill fired
(`tool_used: Skill`), that the server was asked the right question (`regex` over
`mock_calls`), and the answer (a short `llm` rubric). A negative case checks that
neither skill fires on a changelog-writing request.

**Consequences / limits:** the fixtures are a snapshot. When the server's output schema
changes, re-record them and `_tools.json` (commands in `.agents/context/commands.md`)
before trusting a score. A mock returns the same body whatever the input, so a case
cannot show the skill batching correctly. Script behaviour is covered by the unit
tests instead. Runs that grant Bash need the sandbox backend (`bubblewrap` and
`socat`), so the cases grant only read tools and exercise the MCP path.
