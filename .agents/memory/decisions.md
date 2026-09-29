# Architecture decision records

The load-bearing decisions and *why* they hold. One file each, in
[`decisions/`](decisions/) — this page is the router. Open the file whose
row matches; do not guess from the title alone. Supersede a decision by
writing a new ADR and changing the old one's `Status:` line, never by
deleting it.

**This file is generated. Do not edit it by hand.** Add a decision with
`python3 scripts/adr.py new "<title>" --topics a,b`, write the body,
then `python3 scripts/adr.py index`.

**Ids are minted, not chosen.** A new ADR is `YYYY-MM.suffix`
(`ADR 2026-08.k3f9`) with a random suffix, so parallel branches never take
the same number. Cite an ADR by its id, exactly as its heading spells it.

| ADR | Decision | Topics |
| --- | --- | --- |
| [2026-09.d3hx](decisions/2026-09-d3hx-the-product-skills-ship-as.md) | the product skills ship as one plugin under plugins, not in .agents/skills | layout, distribution |
| [2026-09.dqcj](decisions/2026-09-dqcj-evals-answer-from-mocks-recorded.md) | evals answer from mocks recorded off production | evals, testing |
| [2026-09.fm4r](decisions/2026-09-fm4r-each-skill-calls-the-mcp.md) | each skill calls the MCP server and falls back to a stdlib HTTP script | mcp, portability |
| [2026-09.wez2](decisions/2026-09-wez2-private-packages-never-leave-the.md) | private packages never leave the machine, and misses stay recorded | privacy, mcp |
