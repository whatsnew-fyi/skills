"""Unit tests for the skills' scripts. Standard library only:

    python3 -m unittest discover -s tests

The npm, pip and go fixtures are real reports, recorded on 2026-09-28 with home
paths stripped. cargo, dotnet and yarn are written from each tool's documented
format. git-log-declarative-changelog.txt is the real history of the
declarative-changelog CLI, recorded on 2026-09-28 in draft_entry.py's input format.
"""

import filecmp
import glob
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "plugins", "whatsnew", "skills")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


outdated = load_module(
    "outdated_to_deps", os.path.join(SKILLS, "outdated-audit", "scripts", "outdated_to_deps.py")
)
caller = load_module(
    "whatsnew_call", os.path.join(SKILLS, "upgrade-review", "scripts", "whatsnew_call.py")
)
drafter = load_module(
    "draft_entry", os.path.join(SKILLS, "declarative-changelog", "scripts", "draft_entry.py")
)


def fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as handle:
        return handle.read()


def run_converter(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = outdated.main(list(argv))
    batches = [json.loads(line) for line in out.getvalue().splitlines()]
    return code, batches, err.getvalue()


def by_name(deps):
    return {(d["name"], d["from"]): d for d in deps}


class CopiesStayIdentical(unittest.TestCase):
    def test_every_whatsnew_call_is_the_same_file(self):
        copies = sorted(glob.glob(os.path.join(SKILLS, "*", "scripts", "whatsnew_call.py")))
        self.assertGreaterEqual(len(copies), 2)
        for copy in copies[1:]:
            self.assertTrue(
                filecmp.cmp(copies[0], copy, shallow=False),
                f"{copy} differs from {copies[0]}; copy the edited one over the rest",
            )


class LaunchersArePinned(unittest.TestCase):
    """The plugin directory's review refuses a package a launcher runs without an
    exact version, in skill text as much as in a hook or MCP command. evals/ is left
    out: its mocks are vendor release notes recorded verbatim, not commands we run."""

    PLUGIN = os.path.join(ROOT, "plugins", "whatsnew")
    LAUNCH = re.compile(
        r"\b(?:npx|bunx|pnpm dlx|yarn dlx|uvx|pipx run)((?:\s+-{1,2}[\w-]+)*)\s+([@\w][^\s`'\"]*)"
    )
    EXACT = re.compile(r"^(?:@[\w.-]+/)?[\w.-]+(?:@|==)\d+\.\d+\.\d+(?:[-+][\w.-]+)?$")

    def test_every_launched_package_names_an_exact_version(self):
        launched = []
        for path in glob.glob(os.path.join(self.PLUGIN, "**", "*"), recursive=True):
            relative = os.path.relpath(path, self.PLUGIN)
            if relative.startswith("evals" + os.sep) or not os.path.isfile(path):
                continue
            if not path.endswith((".md", ".json", ".py", ".sh", ".yml", ".yaml")):
                continue
            with open(path, encoding="utf-8") as handle:
                for match in self.LAUNCH.finditer(handle.read()):
                    launched.append((relative, match.group(2)))
        self.assertTrue(launched, "expected the declarative-changelog validator launch")
        for relative, package in launched:
            self.assertRegex(package, self.EXACT, f"{relative} runs {package} without an exact version")


class Detection(unittest.TestCase):
    def test_each_fixture_is_detected(self):
        cases = {
            "npm-outdated.json": "npm",
            "pip-outdated.json": "pip",
            "go-list.json": "go",
            "cargo-outdated.json": "cargo",
            "dotnet-outdated.json": "dotnet",
            "yarn-outdated.ndjson": "yarn",
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(outdated.detect(outdated.load(fixture(name))), expected)

    def test_an_empty_npm_report_converts_to_nothing(self):
        self.assertEqual(outdated.convert({}, None)[1], [])

    def test_garbage_is_refused(self):
        with self.assertRaises(ValueError):
            outdated.detect(42)


class Npm(unittest.TestCase):
    def test_workspaces_keep_each_installed_copy_once(self):
        _, deps, _ = outdated.convert(json.loads(fixture("npm-outdated.json")), "npm")
        sdk = [d for d in deps if d["name"] == "@anthropic-ai/sdk"]
        self.assertEqual(sorted(d["from"] for d in sdk), ["0.126.0", "0.128.0"])

    def test_wanted_equal_to_current_is_passed_through(self):
        _, deps, _ = outdated.convert(json.loads(fixture("npm-outdated.json")), "npm")
        babel = by_name(deps)[("@babel/core", "7.29.7")]
        self.assertEqual((babel["wanted"], babel["latest"]), ("7.29.7", "8.0.6"))

    def test_uninstalled_packages_are_skipped(self):
        report = {"left-pad": {"wanted": "1.3.0", "latest": "1.3.0"}}
        fmt, deps, skipped = outdated.convert(report, "npm")
        self.assertEqual(deps, [])
        self.assertEqual(skipped, [("left-pad", "not installed")])


class NpmPrivatePackages(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.node_modules = os.path.join(self.tmp.name, "node_modules")
        self.install("react", {"repository": {"type": "git", "url": "git+https://github.com/facebook/react.git"}})
        self.install("@acme/ui", {"private": True})
        self.install("@acme/client", {"publishConfig": {"registry": "https://npm.acme.test/"}})
        self.install("public-ish", {"publishConfig": {"registry": "https://registry.npmjs.org/"}})
        self.report = os.path.join(self.tmp.name, "outdated.json")
        with open(self.report, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    name: {"current": "1.0.0", "wanted": "1.0.1", "latest": "2.0.0"}
                    for name in ("react", "@acme/ui", "@acme/client", "public-ish", "@corp/tool")
                },
                handle,
            )

    def tearDown(self):
        self.tmp.cleanup()

    def install(self, name, manifest):
        directory = os.path.join(self.node_modules, *name.split("/"))
        os.makedirs(directory)
        with open(os.path.join(directory, "package.json"), "w", encoding="utf-8") as handle:
            json.dump(dict(manifest, name=name, version="1.0.0"), handle)

    def test_private_packages_stay_on_the_machine(self):
        code, batches, err = run_converter(
            self.report, "--node-modules", self.node_modules, "--exclude", "@corp/*"
        )
        self.assertEqual(code, 0)
        sent = {d["name"] for d in batches[0]["dependencies"]}
        self.assertEqual(sent, {"react", "public-ish"})
        for name in ("@acme/ui", "@acme/client", "@corp/tool"):
            self.assertIn(f"skipped {name}", err)

    def test_repository_comes_from_the_installed_manifest(self):
        _, batches, _ = run_converter(self.report, "--node-modules", self.node_modules)
        react = by_name(batches[0]["dependencies"])[("react", "1.0.0")]
        self.assertEqual(react["repository"], "git+https://github.com/facebook/react.git")


class OtherEcosystems(unittest.TestCase):
    def test_pip_goes_to_pypi_with_latest_only(self):
        _, deps, _ = outdated.convert(json.loads(fixture("pip-outdated.json")), None)
        django = by_name(deps)[("django", "4.2")]
        self.assertEqual(django, {"name": "django", "from": "4.2", "latest": "6.1.1", "registry": "pypi"})

    def test_go_skips_the_main_module_and_current_modules(self):
        _, deps, _ = outdated.convert(outdated.load(fixture("go-list.json")), None)
        self.assertEqual(len(deps), 5)
        self.assertTrue(all(d["purl"] == "pkg:golang/" + d["name"] for d in deps))
        self.assertFalse(any(d["name"].startswith("/") for d in deps))

    def test_cargo_maps_compat_to_wanted_and_drops_placeholders(self):
        _, deps, skipped = outdated.convert(json.loads(fixture("cargo-outdated.json")), None)
        found = by_name(deps)
        self.assertEqual(found[("serde", "1.0.100")]["wanted"], "1.0.228")
        self.assertNotIn("wanted", found[("clap", "3.2.25")])
        self.assertEqual(skipped, [("old-crate", "no project version")])

    def test_dotnet_dedupes_across_frameworks_and_uses_purls(self):
        _, deps, _ = outdated.convert(json.loads(fixture("dotnet-outdated.json")), None)
        self.assertEqual([d["name"] for d in deps], ["Newtonsoft.Json", "Serilog"])
        self.assertEqual(deps[0]["purl"], "pkg:nuget/Newtonsoft.Json")

    def test_yarn_reads_the_table_row(self):
        _, deps, _ = outdated.convert(outdated.load(fixture("yarn-outdated.ndjson")), None)
        react = by_name(deps)[("react", "18.2.0")]
        self.assertEqual((react["wanted"], react["latest"]), ("18.3.1", "19.2.0"))


class Batching(unittest.TestCase):
    def test_batches_hold_at_most_one_hundred(self):
        report = {f"pkg-{i}": {"current": "1.0.0", "latest": "2.0.0"} for i in range(230)}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(report, handle)
        try:
            _, batches, err = run_converter(handle.name, "--node-modules", "/nonexistent")
        finally:
            os.unlink(handle.name)
        self.assertEqual([len(b["dependencies"]) for b in batches], [100, 100, 30])
        self.assertIn("230 packages in 3 batch(es)", err)


class FakeResponse:
    def __init__(self, body, content_type):
        self.body, self.headers = body.encode("utf-8"), {"content-type": content_type}

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class WhatsnewCall(unittest.TestCase):
    def invoke(self, body, content_type="text/event-stream"):
        out, err = io.StringIO(), io.StringIO()
        stdin = io.StringIO('{"dependencies": [{"name": "next", "from": "16.2.0"}]}')
        with mock.patch.object(caller.urllib.request, "urlopen", return_value=FakeResponse(body, content_type)) as urlopen, \
                mock.patch.object(sys, "stdin", stdin), redirect_stdout(out), redirect_stderr(err):
            code = caller.main(["whatsnew_call.py", "missing_changes"])
        return code, out.getvalue(), err.getvalue(), urlopen

    def test_sse_reply_prints_structured_content(self):
        reply = {"result": {"content": [{"type": "text", "text": "{}"}], "structuredContent": {"summary": {"tracked": 1}}}}
        code, out, _, urlopen = self.invoke(f"event: message\ndata: {json.dumps(reply)}\n\n")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"summary": {"tracked": 1}})
        sent = json.loads(urlopen.call_args[0][0].data)
        self.assertEqual(sent["params"], {"name": "missing_changes", "arguments": {"dependencies": [{"name": "next", "from": "16.2.0"}]}})

    def test_plain_json_reply_falls_back_to_text_content(self):
        reply = {"result": {"content": [{"type": "text", "text": '{"ok": true}'}]}}
        code, out, _, _ = self.invoke(json.dumps(reply), "application/json")
        self.assertEqual((code, json.loads(out)), (0, {"ok": True}))

    def test_a_refusal_exits_two_with_the_message(self):
        reply = {"result": {"content": [{"type": "text", "text": "Unknown product"}], "isError": True}}
        code, out, err, _ = self.invoke(f"data: {json.dumps(reply)}\n")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("Unknown product", err)

    def test_a_protocol_error_exits_one(self):
        reply = {"error": {"code": -32602, "message": "Invalid params"}}
        code, _, err, _ = self.invoke(f"data: {json.dumps(reply)}\n")
        self.assertEqual(code, 1)
        self.assertIn("Invalid params", err)


# The spec's release-heading grammar, for checking what the drafter prints.
RELEASE_HEADING = re.compile(
    r"^## (?:(?:\[[^\]]+\]\([^)]+\)|[^\[].*?) (?:—|–|-) )?"
    r"\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?"
    r"(?: \((?:yanked|routine)(?:, (?:yanked|routine))*\))?$"
)


def log(*commits):
    """draft_entry's stdin format from (subject, body) pairs."""
    return "".join(f"{i:040x}\x1f{subject}\x1f{body}\x1e\n" for i, (subject, body) in enumerate(commits))


def run_drafter(stdin, *argv):
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(stdin)), redirect_stdout(out), redirect_stderr(err):
        code = drafter.main(["--stdin", "--date", "2026-09-28", *argv])
    return code, out.getvalue(), err.getvalue()


def sections_of(entry):
    """{category: [item lines]} from a drafted entry."""
    found, current = {}, None
    for line in entry.splitlines():
        if line.startswith("### "):
            current = found.setdefault(line[4:], [])
        elif line.startswith("- ") and current is not None:
            current.append(line[2:])
    return found


class DraftEntry(unittest.TestCase):
    def test_the_recorded_history_drafts_a_categorized_entry(self):
        code, out, err = run_drafter(fixture("git-log-declarative-changelog.txt"), "--previous", "0.1.0")
        self.assertEqual(code, 0)
        heading = out.splitlines()[0]
        self.assertEqual(heading, "## 0.2.0 — 2026-09-28")
        self.assertRegex(heading, RELEASE_HEADING)
        sections = sections_of(out)
        self.assertEqual(list(sections), ["Added", "Fixed"])
        self.assertEqual(
            sections["Fixed"],
            ["**Breaking** — frontmatter: accept bare hex product.color and explain empty values"],
        )
        self.assertEqual(len(sections["Added"]), 3)
        self.assertTrue(sections["Added"][0].startswith("**Breaking** — "))
        self.assertEqual(sections["Added"][-1], "implement declarative changelog validator and parser")
        self.assertIn("9 commits: 4 mapped, 5 hidden, 0 unclassified", err)
        self.assertIn("hidden types: build, chore, ci, test", err)
        self.assertIn("suggested bump: minor (0.1.0 → 0.2.0)", err)

    def test_a_breaking_change_footer_becomes_the_items_detail(self):
        _, out, _ = run_drafter(fixture("git-log-declarative-changelog.txt"))
        self.assertIn(
            "\n  parsed `product.color` no longer carries a leading `#`; "
            "consumers expecting `#RRGGBB` now receive `RRGGBB`.\n",
            out,
        )

    def test_every_type_lands_in_its_category_in_canonical_order(self):
        stdin = log(
            ("security: reject path traversal in archive names", ""),
            ("remove: drop the legacy config loader", ""),
            ("fix(cli): exit 2 on a missing file (#12)", ""),
            ("deprecate: the --serial flag", ""),
            ("perf: cache parsed headings", ""),
            ('Revert "feat: add colour output"', ""),
            ("feat: add --json output", ""),
        )
        _, out, _ = run_drafter(stdin)
        sections = sections_of(out)
        self.assertEqual(list(sections), list(drafter.CATEGORIES))
        self.assertEqual(sections["Changed"], ["cache parsed headings", "Revert feat: add colour output"])
        self.assertEqual(sections["Fixed"], ["cli: exit 2 on a missing file (#12)"])

    def test_breaking_items_lead_their_section(self):
        stdin = log(("feat: add --json output", ""), ("feat!: drop Node 18", ""))
        _, out, err = run_drafter(stdin, "--previous", "v1.4.2")
        self.assertEqual(sections_of(out)["Added"], ["**Breaking** — drop Node 18", "add --json output"])
        self.assertTrue(out.startswith("## v2.0.0 — "))
        self.assertIn("suggested bump: major (v1.4.2 → v2.0.0)", err)

    def test_a_breaking_refactor_is_not_hidden(self):
        stdin = log(("refactor(api): rename Client.get", "BREAKING CHANGE: use Client.fetch.\n"))
        _, out, _ = run_drafter(stdin)
        self.assertEqual(sections_of(out)["Changed"], ["**Breaking** — api: rename Client.get"])

    def test_only_hidden_types_draft_a_routine_release(self):
        stdin = log(("chore(deps): bump yaml", ""), ("ci: cache npm", ""))
        _, out, err = run_drafter(stdin, "--previous", "1.2.3", "--url", "https://x.example/r/v{version}")
        heading = out.splitlines()[0]
        self.assertEqual(heading, "## [1.2.4](https://x.example/r/v1.2.4) — 2026-09-28 (routine)")
        self.assertRegex(heading, RELEASE_HEADING)
        self.assertNotIn("### ", out)
        self.assertIn("nothing reader-facing", err)

    def test_unconventional_subjects_are_reported_not_dropped(self):
        stdin = log(("Update README", ""), ("wip: try things", ""), ("fix: typo in help", ""))
        _, out, err = run_drafter(stdin)
        self.assertEqual(sections_of(out), {"Fixed": ["typo in help"]})
        self.assertIn("unclassified: 0000000 Update README", err)
        self.assertIn("wip: try things", err)

    def test_without_a_version_the_heading_is_date_only(self):
        _, out, err = run_drafter(log(("fix: typo", "")))
        self.assertEqual(out.splitlines()[0], "## 2026-09-28")
        self.assertIn("pass --version", err)

    def test_zero_major_breaking_bumps_the_minor(self):
        _, out, _ = run_drafter(log(("feat!: new heading grammar", "")), "--previous", "0.4.1")
        self.assertTrue(out.startswith("## 0.5.0 — "))

    def test_a_bad_git_range_exits_two(self):
        err = io.StringIO()
        with redirect_stderr(err), redirect_stdout(io.StringIO()):
            code = drafter.main(["--since", "no-such-ref-anywhere", "--until", "no-such-ref-either"])
        self.assertEqual(code, 2)
        self.assertIn("draft_entry:", err.getvalue())


if __name__ == "__main__":
    unittest.main()
