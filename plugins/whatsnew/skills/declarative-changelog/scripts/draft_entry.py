#!/usr/bin/env python3
"""Draft one Declarative Changelog release entry from Conventional Commits.

    python3 draft_entry.py                              # commits since the latest tag
    python3 draft_entry.py --since v1.4.0 --version 2.0.0 \\
        --url 'https://github.com/acme/kestrel/releases/tag/v{version}'
    git log --no-merges --format='%H%x1f%s%x1f%b%x1e' v1.4.0..HEAD | python3 draft_entry.py --stdin

Reads the commits with a read-only `git log` (or from stdin in that format),
maps each commit type to a category the way the spec's "Generating this from
Conventional Commits" table does, and prints a draft `## ` entry to stdout:
sections in canonical order, breaking items opened with the exact
`**Breaking** — ` marker, and `(routine)` when nothing reader-facing remains.
The summary is a placeholder, because generation cannot write it.

What was mapped, hidden and left unclassified, and the suggested semver bump,
go to stderr. Nothing is written to disk.

Exit 0 on success, 2 on bad arguments or a git range that does not resolve.

Standard library only; Python 3.8+.
"""

import argparse
import datetime
import re
import subprocess
import sys

CATEGORIES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")

TYPE_CATEGORY = {
    "feat": "Added",
    "fix": "Fixed",
    "perf": "Changed",
    "revert": "Changed",
    "security": "Security",
    "deprecate": "Deprecated",
    "remove": "Removed",
}
HIDDEN = ("docs", "style", "refactor", "test", "build", "ci", "chore")

SUBJECT = re.compile(r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()]*)\))?(?P<bang>!)?: +(?P<desc>\S.*)$")
GIT_REVERT = re.compile(r'^Revert "(?P<desc>.+)"$')
BREAKING_FOOTER = re.compile(r"^BREAKING[ -]CHANGE: *(?P<text>.*)$")
FOOTER_TOKEN = re.compile(r"^(?:[A-Za-z-]+|BREAKING CHANGE)(?:: | #)")
VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")

FIELD, RECORD = "\x1f", "\x1e"
GIT_FORMAT = "%H%x1f%s%x1f%b%x1e"
SUMMARY_PLACEHOLDER = "> TODO: one sentence on what this release changes for a reader."


class Commit:
    def __init__(self, sha, subject, body):
        self.sha = sha
        self.subject = subject.strip()
        self.body = body or ""


def parse_log(text):
    """Commits from `git log --format=%H%x1f%s%x1f%b%x1e` output."""
    commits = []
    for record in text.split(RECORD):
        record = record.strip("\n")
        if not record.strip():
            continue
        parts = record.split(FIELD)
        while len(parts) < 3:
            parts.append("")
        commits.append(Commit(parts[0].strip(), parts[1], FIELD.join(parts[2:])))
    return commits


def breaking_note(body):
    """The text of a BREAKING CHANGE footer, joined onto one line, or None."""
    lines, note = body.splitlines(), None
    for line in lines:
        if note is None:
            match = BREAKING_FOOTER.match(line.strip())
            if match:
                note = [match.group("text").strip()]
            continue
        stripped = line.strip()
        if not stripped or FOOTER_TOKEN.match(stripped):
            break
        note.append(stripped)
    if note is None:
        return None
    return " ".join(part for part in note if part) or None


def classify(commit):
    """(category or None, item text, breaking, detail) — category None means hidden.

    Returns None for a subject that is not a Conventional Commit.
    """
    revert = GIT_REVERT.match(commit.subject)
    if revert:
        return "Changed", "Revert " + revert.group("desc"), False, None
    match = SUBJECT.match(commit.subject)
    if not match:
        return None
    kind = match.group("type").lower()
    if kind not in TYPE_CATEGORY and kind not in HIDDEN:
        return None
    note = breaking_note(commit.body)
    breaking = bool(match.group("bang")) or note is not None
    text = match.group("desc").strip()
    if match.group("scope"):
        text = "{}: {}".format(match.group("scope").strip(), text)
    category = TYPE_CATEGORY.get(kind)
    if category is None and breaking:
        # A breaking refactor or build change still breaks readers; it cannot stay hidden.
        category = "Changed"
    return category, text, breaking, note


def draft(commits):
    """Group commits into sections; report what was hidden and unclassified."""
    sections = {name: [] for name in CATEGORIES}
    hidden, unclassified = [], []
    for commit in commits:
        result = classify(commit)
        if result is None:
            unclassified.append(commit)
            continue
        category, text, breaking, note = result
        if category is None:
            hidden.append(commit)
            continue
        sections[category].append((breaking, text, note))
    for name in CATEGORIES:
        # Breaking items first; otherwise keep the log's order.
        sections[name].sort(key=lambda item: not item[0])
    return sections, hidden, unclassified


def parse_version(value):
    match = VERSION.match(value or "")
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def suggest_bump(sections):
    if any(breaking for items in sections.values() for breaking, _, _ in items):
        return "major"
    if sections["Added"] or sections["Deprecated"]:
        return "minor"
    return "patch"


def effective_bump(previous, bump):
    """While 0.x, a breaking change bumps the minor."""
    parts = parse_version(previous)
    if bump == "major" and parts is not None and parts[0] == 0:
        return "minor"
    return bump


def bumped(previous, bump):
    """The next version after `previous`, or None when it is not a version."""
    parts = parse_version(previous)
    if parts is None:
        return None
    major, minor, patch = parts
    bump = effective_bump(previous, bump)
    if bump == "major":
        nxt = "{}.0.0".format(major + 1)
    elif bump == "minor":
        nxt = "{}.{}.0".format(major, minor + 1)
    else:
        nxt = "{}.{}.{}".format(major, minor, patch + 1)
    return ("v" + nxt) if previous.startswith("v") else nxt


def heading(version, url, date, routine):
    label = ""
    if version:
        label = "[{}]({})".format(version, url.replace("{version}", version.lstrip("v"))) if url else version
    elif url:
        label = None  # A permalink with no version has nothing to hang on; the hatch carries it.
    text = "## " + (label + " — " if label else "") + date
    if routine:
        text += " (routine)"
    return text


def render(sections, version, url, date):
    routine = not any(sections.values())
    lines = [heading(version, url, date, routine), ""]
    if url and not version:
        lines += ["```changelog", "url: " + url, "```", ""]
    lines += [SUMMARY_PLACEHOLDER, ""]
    for name in CATEGORIES:
        items = sections[name]
        if not items:
            continue
        lines += ["### " + name, ""]
        for breaking, text, note in items:
            lines.append("- " + ("**Breaking** — " if breaking else "") + text)
            if note:
                lines += ["", "  " + note, ""]
        if lines[-1] != "":
            lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def git(*args):
    result = subprocess.run(
        ("git",) + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git {} failed".format(" ".join(args)))
    return result.stdout


def latest_tag():
    try:
        return git("describe", "--tags", "--abbrev=0").strip() or None
    except RuntimeError:
        return None


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--since", help="range start, exclusive (default: the latest tag)")
    parser.add_argument("--until", default="HEAD", help="range end (default: HEAD)")
    parser.add_argument("--stdin", action="store_true", help="read git log output from stdin")
    parser.add_argument("--version", dest="release", help="version for the heading (default: suggested)")
    parser.add_argument("--previous", help="the version this release follows, for the bump")
    parser.add_argument("--url", help="release permalink; {version} is replaced, without its v")
    parser.add_argument("--date", help="RFC 3339 date or timestamp (default: now, UTC)")
    args = parser.parse_args(argv)

    since = args.since
    if args.stdin:
        text = sys.stdin.read()
    else:
        if since is None:
            since = latest_tag()
        rev_range = "{}..{}".format(since, args.until) if since else args.until
        try:
            text = git("log", "--no-merges", "--format=" + GIT_FORMAT, rev_range)
        except (RuntimeError, OSError) as error:
            print("draft_entry: {}".format(error), file=sys.stderr)
            return 2
        print("range: {}".format(rev_range if since else args.until + " (no tag found: whole history)"),
              file=sys.stderr)

    commits = parse_log(text)
    sections, hidden, unclassified = draft(commits)
    previous = args.previous or (since if parse_version(since) else None)
    bump = effective_bump(previous, suggest_bump(sections))
    suggested = bumped(previous, bump) if previous else None
    release = args.release or suggested

    print(render(sections, release, args.url, args.date or now()), end="")

    mapped = sum(len(items) for items in sections.values())
    print("{} commits: {} mapped, {} hidden, {} unclassified".format(
        len(commits), mapped, len(hidden), len(unclassified)), file=sys.stderr)
    if hidden:
        kinds = sorted({SUBJECT.match(c.subject).group("type").lower() for c in hidden})
        print("hidden types: " + ", ".join(kinds), file=sys.stderr)
    for commit in unclassified:
        print("unclassified: {} {}".format(commit.sha[:7], commit.subject), file=sys.stderr)
    if not mapped:
        print("nothing reader-facing: drafted as (routine)", file=sys.stderr)
    if suggested:
        print("suggested bump: {} ({} → {})".format(bump, previous, suggested), file=sys.stderr)
    else:
        print("suggested bump: {} (pass --previous to compute the version)".format(bump), file=sys.stderr)
    if not release:
        print("no version: the heading is date-only; pass --version", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
