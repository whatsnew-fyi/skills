# Release tools that write the changelog

When a tool writes `CHANGELOG.md`, configure the tool. An entry written by hand is
overwritten or left behind at the next release, and the next generated entry fails the
check again.

Every configuration here is tested against the real tool in the validator's repository,
at the tag that matches the pinned validator:
<https://github.com/whatsnew-fyi/declarative-changelog/tree/v0.4.0/templates>. CI runs
each tool over a fixture repository and requires Level 2 with no warnings. The commit
types map to categories as in [`format.md`](format.md#from-conventional-commits).

## Which tool writes the file

| Look for | Tool | How it conforms |
| --- | --- | --- |
| `cliff.toml`, `.cliff.toml`, or a `git-cliff` table in `Cargo.toml` or `pyproject.toml` | git-cliff | Configuration alone |
| `release.config.*`, `.releaserc*`, or a `release` key in `package.json` | semantic-release | Configuration alone |
| `.versionrc*`, or `commit-and-tag-version` or `standard-version` in `package.json` | commit-and-tag-version | Configuration alone |
| `release-please-config.json`, or `googleapis/release-please-action` in a workflow | release-please | Its sections, then `normalize` on the release PR |
| a `.changeset/` directory | Changesets | `changeset version`, then `normalize` |
| `.goreleaser.yml` or `.goreleaser.yaml` | GoReleaser | Reads the file: `extract` gives it the tag's entry |

## Full configurations

git-cliff, semantic-release and commit-and-tag-version take a whole configuration
file. Fetch it from `https://raw.githubusercontent.com/whatsnew-fyi/declarative-changelog/v0.4.0/templates/<path>`
when you can; when you can't, give the user the link. **Don't write one of these from
memory.** Each works around a specific quirk of its tool, and a plausible-looking
config that misses one fails at the next release.

| Tool | Path | Then change | Needs |
| --- | --- | --- | --- |
| git-cliff | `git-cliff/cliff.toml` | the product name in `header`, the URL in `postprocessors` | git-cliff 2.14.1 or later |
| semantic-release | `semantic-release/release.config.mjs` | the frontmatter in `TITLE` | semantic-release 24 or later, `@semantic-release/changelog`, `@semantic-release/git` |
| commit-and-tag-version | `commit-and-tag-version/.versionrc.mjs` | the frontmatter in `header` | commit-and-tag-version 13 or later, Node 22.12 or later |

Merge into the project's existing configuration rather than replacing it: keep its
branches, plugins, tag format and anything else the release depends on.

- **git-cliff:** `git cliff -o CHANGELOG.md` writes the file from the tags;
  `git cliff --unreleased --tag v1.2.0 --prepend CHANGELOG.md` adds one release.
- **semantic-release:** its frontmatter has no `document.updated`, because the
  changelog plugin finds the title by its exact text.
- **commit-and-tag-version:** start from an empty file, or run it once with
  `--release-count 0` to write every release from the tags. The title must not be
  exactly `# Changelog`, or the frontmatter is copied twice. `standard-version` is
  unmaintained; this needs its successor.

## release-please

release-please writes `## [1.2.0](compare) (2026-10-14)`, which the heading grammar
rejects, and a `### ⚠ BREAKING CHANGES` section. No setting changes either, so the
workflow repairs each release PR.

1. Add `changelog-sections` to each package in `release-please-config.json`. Hidden
   types keep a section so a breaking one still lands somewhere:

   ```json
   "changelog-sections": [
     { "type": "feat", "section": "Added" },
     { "type": "perf", "section": "Changed" },
     { "type": "revert", "section": "Changed" },
     { "type": "deprecate", "section": "Deprecated" },
     { "type": "remove", "section": "Removed" },
     { "type": "fix", "section": "Fixed" },
     { "type": "security", "section": "Security" },
     { "type": "docs", "section": "Changed", "hidden": true },
     { "type": "style", "section": "Changed", "hidden": true },
     { "type": "refactor", "section": "Changed", "hidden": true },
     { "type": "test", "section": "Changed", "hidden": true },
     { "type": "build", "section": "Changed", "hidden": true },
     { "type": "ci", "section": "Changed", "hidden": true },
     { "type": "chore", "section": "Changed", "hidden": true }
   ]
   ```

2. Give the action an `id` and add these steps after it. They run `normalize` on the
   release PR's branch each time release-please rebuilds it:

   ```yaml
   - id: release
     uses: googleapis/release-please-action@v5

   - if: steps.release.outputs.prs_created == 'true'
     uses: actions/checkout@v7
     with:
       ref: ${{ fromJSON(steps.release.outputs.pr).headBranchName }}

   - if: steps.release.outputs.prs_created == 'true'
     run: |
       npx --yes declarative-changelog@0.4.0 normalize --write CHANGELOG.md
       if ! git diff --quiet; then
         git config user.name "github-actions[bot]"
         git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
         git commit --all --message "chore: normalize CHANGELOG.md"
         git push
       fi
   ```

   The job needs `contents: write` and `pull-requests: write`.

3. If the file has no release yet, put `## [Unreleased]` under the title. release-please
   inserts above the first heading that starts with `[` or a version; with none, it
   writes above the frontmatter. `normalize` moves Unreleased back to the top after
   every release.

## Changesets

Changesets writes an undated `## 1.2.0` under Major, Minor and Patch Changes, inside
the frontmatter until the file has a heading that starts with a version. `normalize`
moves the entry out, dates it, and files Major as Changed with the Breaking marker,
Minor as Added and Patch as Fixed.

1. Add `declarative-changelog` as a dev dependency at exactly `0.4.0`, and a script:

   ```json
   "version-packages": "changeset version && declarative-changelog normalize --write CHANGELOG.md"
   ```

   A monorepo names every package's file, say `packages/*/CHANGELOG.md`.

2. Point the action at it. `changesets/action@v2` calls the input `version-script`; v1
   called it `version`:

   ```yaml
   - uses: changesets/action@v2
     with:
       version-script: npm run version-packages
   ```

The date is when the version PR was last rebuilt.

## GoReleaser

GoReleaser writes release notes, not a changelog. Keep `CHANGELOG.md` as the one place
notes are written and hand GoReleaser the tag's entry. `extract` exits 1 when there is
none, so a tag pushed before its notes fails the job instead of shipping empty notes:

```yaml
- run: npx --yes declarative-changelog@0.4.0 extract CHANGELOG.md "$GITHUB_REF_NAME" > "$RUNNER_TEMP/notes.md"
- uses: goreleaser/goreleaser-action@v7
  with:
    version: "~> v2"
    args: release --clean --release-notes ${{ runner.temp }}/notes.md
```

The same `extract` step fills any release body, for example `body_path` in
`softprops/action-gh-release`.

## What no tool writes

The summary blockquote. Choosing which of forty commits mattered is an editorial call.
Write it into the release PR (release-please, Changesets) or into the new entry after a
tool that edits only that entry. Regenerating the whole file from the tags writes over
it, so say so when the project does that.
