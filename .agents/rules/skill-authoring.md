# Skill authoring

Standing rules for every skill under `plugins/whatsnew/skills/`. They hold for
new skills too.

## A skill earns its install on its own

- **It must help someone who has never heard of What's New.** The skill answers a
  developer's question: is this upgrade safe, what is this project missing. What's
  New is where the answer comes from. It is never the pitch.
- **Credit the source once per answer.** Link the release permalinks and the vendor's
  own notes, and credit What's New (whatsnew.fyi) as the source of the release data.
  No taglines, calls to action or "powered by" footers.

## The description is the trigger

- The `description` frontmatter decides whether the skill ever runs. Say what it
  does, then when to use it, in the words a user types and the files they touch:
  `package.json`, "Dependabot", `npm outdated`, "is it safe to upgrade".
- Keep it under 1,024 characters, which is the Agent Skills limit.
- A change to a description is a behaviour change. Re-run the evals, including the
  negative case, which checks that neither skill fires on unrelated requests.

## Instructions name only real fields

- Every field, status or flag a `SKILL.md` names must exist in the live output schema.
  `plugins/whatsnew/evals/mocks/whatsnew/_tools.json` is that schema as recorded.
  Refresh it before relying on it (see `.agents/context/commands.md`).
- When a result can be cut (`truncated`, `sectionsOmitted`, `changesTruncated`), the
  skill must say where the rest is (`compareMarkdownUrl`) before the agent concludes
  anything.

## Claims stay inside the data

- Silence is never safety. A skill must not let the agent say "no breaking changes"
  or "no security issues" from an `untracked` status, zero tracked releases or a cut
  result.
- Vendor breaking-change and migration text is quoted, not paraphrased.

## Scripts

- Python 3.8+, standard library only, with no install step. A skill that needs `pip
  install` first will not get used.
- A script never writes into the user's repository, and never runs a package manager
  that changes state (`npm update`, `pip install`). The dependency skills audit and
  review, and the user decides what changes. `declarative-changelog` is the one skill
  whose agent edits a file, and only the changelog the user asked about (ADR
  2026-09.vyb9).
- A script shared between skills is copied into each one (ADR 2026-09.fm4r). Edit one
  copy, then copy it over the others. `tests/test_scripts.py` fails while they differ.
- Package names the server can never track stay on the machine (ADR 2026-09.wez2).

## The changelog format has an owner

- `declarative-changelog` teaches a draft standard this repository does not own. Its
  source of truth is `whatsnew-app` (`src/app/spec/content.md`, served at
  <https://whatsnew.fyi/spec.md>). The validator's closed vocabularies live in the
  `declarative-changelog` npm package (`src/constants.ts`). When either changes,
  refresh `references/format.md` and the pinned `declarative-changelog@<version>` in the
  skill, the CIs and `.agents/context/commands.md`, together.
- The pin is an exact version (`@0.2.0`), never a range (`@0.2`) or a bare package
  name, anywhere in the plugin folder: frontmatter, skill text, references and
  README. The plugin directory's review refuses a range, and
  `tests/test_scripts.py` (`LaunchersArePinned`) fails on one.

## Every change ships with its evidence

- A new skill gets at least one eval case that checks it fires and one grader on its
  answer. A behaviour change updates the case it affects.
- A script change gets a unit test against a real recorded report in
  `tests/fixtures/`. Strip home-directory paths out of recorded fixtures.
- A user-visible change gets a `CHANGELOG.md` entry and a `version` bump in
  `plugins/whatsnew/.claude-plugin/plugin.json`, together (see
  `.agents/context/distribution.md`).
