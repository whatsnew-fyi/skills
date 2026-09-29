# Commands

Everything runs from the repository root. There is no build step and nothing to
install for the checks except the Claude Code CLI and Node for `npx`.

## Finishing checks

A change is finished when all of these pass. CI runs the first four.

```sh
python3 -m unittest discover -s tests                 # the skills' scripts
claude plugin validate --strict .                      # marketplace manifest
claude plugin validate --strict plugins/whatsnew       # plugin, skills, .mcp.json
python3 scripts/adr.py index --check                   # decisions router is current
npx -y declarative-changelog@0.1 validate CHANGELOG.md --require-level 2 --max-warnings 0
```

`.claude/hooks/lintorama-stop.sh` runs the `zaventh/lintorama` container (shellcheck,
markdownlint, yamllint, actionlint) as a Stop hook and blocks the turn until its
findings are fixed; it no-ops without Docker. Config: `.mdlrc` (relaxed; MD029 off
because step numbering is intentional) and `.yamllint` (relaxed, no line-length).
Run it by hand with:

```sh
docker run --rm -v "$PWD":/code -v "$PWD"/.git:/code/.git zaventh/lintorama:6
```

The evals are the fifth check, run by hand because they call the model and cost
money. Run them after any change to a `SKILL.md`, and especially to a
`description`:

```sh
cd plugins/whatsnew
claude plugin eval . --scaffold --trust-plugin -j 2 --no-publish --judge-model sonnet
```

- `--scaffold` runs the cases' own `fixture.sh`, which is safe because this repo
  wrote them.
- Each case runs 3 times in each of two arms (with and without the plugin), so the
  suite is about 6 × cases agent runs. Keep `-j` low: this is a laptop.
- `--judge-model sonnet`: the default judge (Haiku) splits votes on these rubrics
  even when the answer is right.
- `--ablation none` halves the cost while you iterate on graders, and
  `--keep-temp` keeps each run's `trace.jsonl` so you can read what it answered.
- Results go to `plugins/whatsnew/evals/results/`, which is gitignored.
- A case that grants `Bash` needs the sandbox backend (`bubblewrap` and `socat`).
  Without it the run is refused rather than run unconfined, so the cases grant
  read-only tools (ADR 2026-09.dqcj).

## Try a skill against production

```sh
python3 plugins/whatsnew/skills/outdated-audit/scripts/outdated_to_deps.py tests/fixtures/pip-outdated.json |
  python3 plugins/whatsnew/skills/outdated-audit/scripts/whatsnew_call.py missing_changes
```

Or install the plugin from this checkout. Remove it afterwards: it is written to
your user settings.

```sh
claude plugin marketplace add ./
claude plugin install whatsnew@whatsnew-fyi
claude plugin details whatsnew                 # expect Skills (2), MCP servers (1)
claude plugin marketplace remove whatsnew-fyi  # uninstalls its plugins too
```

## Re-record the eval mocks from production

Do this when the server's output schema changes (ADR 2026-09.dqcj):

```sh
M=plugins/whatsnew/evals/mocks/whatsnew
call() { curl -s -X POST https://whatsnew.fyi/mcp -H 'content-type: application/json' \
  -H 'accept: application/json, text/event-stream' -d "$1" | sed -n 's/^data: //p'; }
call '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 -c \
  'import json,sys; json.dump(json.load(sys.stdin)["result"], open(sys.argv[1],"w"), indent=1, ensure_ascii=False)' "$M/_tools.json"
echo '{"dependencies":[{"name":"better-auth","from":"1.6.0","to":"1.7.0"}],"recordMisses":false}' |
  python3 $M/../../../skills/upgrade-review/scripts/whatsnew_call.py upgrade_notes > "$M/fixtures/better-auth-1.6.0-1.7.0.json"
```

The `missing_changes` fixture is the same call with the three packages in
`evals/outdated-audit-npm-report/prompt.md`. The rubrics quote numbers from the
fixtures, so re-read `graders/*.md` after re-recording.

## Decisions

```sh
python3 scripts/adr.py new "<the decision, as a claim>" --topics a,b
python3 scripts/adr.py index
python3 scripts/adr.py lint     # markdownlint via lintorama (docker), exit 3 if unavailable
```
