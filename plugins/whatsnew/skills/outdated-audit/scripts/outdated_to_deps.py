#!/usr/bin/env python3
"""Turn a package manager's outdated report into missing_changes arguments.

    npm outdated --json > outdated.json          # exits 1 when anything is outdated
    python3 outdated_to_deps.py outdated.json --exclude '@acme/*'

Reads the report from a file or stdin, detects its format, and prints one JSON
object per line, each a complete `missing_changes` argument object of at most
100 dependencies (the tool's cap). A summary of what was converted and what was
skipped goes to stderr.

Formats: npm / pnpm `outdated --json`, yarn classic `outdated --json`,
pip / uv `list --outdated --format json`, `go list -m -u -json all`,
`cargo outdated --format json`, `dotnet list package --outdated --format json`.

Private packages are left out rather than sent: anything matching --exclude,
and on npm any installed package marked "private" (a workspace) or whose
publishConfig names a registry other than npmjs.org. The server cannot track them, so sending them buys nothing.

Standard library only; Python 3.8+.
"""

import argparse
import fnmatch
import json
import os
import sys

BATCH = 100
PUBLIC_NPM = ("https://registry.npmjs.org", "https://registry.yarnpkg.com")


def load(text):
    """One JSON document, a stream of concatenated objects (go), or NDJSON (yarn)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    decoder, docs, i = json.JSONDecoder(), [], 0
    while i < len(text):
        doc, i = decoder.raw_decode(text, i)
        docs.append(doc)
        while i < len(text) and text[i].isspace():
            i += 1
    return docs


def detect(doc):
    if isinstance(doc, list):
        if doc and all(isinstance(d, dict) and "Path" in d for d in doc):
            return "go"
        if doc and all(isinstance(d, dict) and d.get("type") for d in doc):
            return "yarn"
        if all(isinstance(d, dict) and "latest_version" in d for d in doc):
            return "pip"
    if isinstance(doc, dict):
        if "Path" in doc:
            return "go"
        if "projects" in doc:
            return "dotnet"
        if isinstance(doc.get("dependencies"), list):
            return "cargo"
        values = list(doc.values())
        if all(isinstance(v, (dict, list)) for v in values):
            return "npm"
    raise ValueError("unrecognized outdated report; pass --format")


def version(value):
    """A concrete version, or None for the placeholders tools print instead."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value in ("", "---", "-", "Removed", "exotic", "linked", "git", "MISSING"):
        return None
    return value


def dep(name, current, wanted=None, latest=None, **extra):
    entry = {"name": name, "from": current}
    # Pass what the tool reported, even wanted == from: that is the answer
    # "nothing is reachable inside the declared range", not a missing field.
    if wanted:
        entry["wanted"] = wanted
    if latest:
        entry["latest"] = latest
    entry.update({k: v for k, v in extra.items() if v})
    return entry


def npm_repository(node_modules, name):
    """The installed package's repository and whether it came from a private registry."""
    if not node_modules:
        return None, False
    path = os.path.join(node_modules, *name.split("/"), "package.json")
    try:
        with open(path, encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError):
        return None, False
    registry = (manifest.get("publishConfig") or {}).get("registry", "")
    # "private": true is a workspace or linked package that was never published.
    private = manifest.get("private") is True or (
        bool(registry) and not registry.rstrip("/").startswith(PUBLIC_NPM)
    )
    repository = manifest.get("repository")
    if isinstance(repository, dict):
        repository = repository.get("url")
    return (repository if isinstance(repository, str) else None), private


def from_npm(doc, node_modules, skipped):
    seen = set()
    for name, rows in doc.items():
        for row in rows if isinstance(rows, list) else [rows]:
            current = version(row.get("current"))
            if not current:
                skipped.append((name, "not installed"))
                continue
            key = (name, current)
            if key in seen:
                continue
            seen.add(key)
            repository, private = npm_repository(node_modules, name)
            if private:
                skipped.append((name, "private (workspace or private registry)"))
                continue
            yield dep(
                name,
                current,
                version(row.get("wanted")),
                version(row.get("latest")),
                repository=repository,
            )


def from_yarn(docs, node_modules, skipped):
    for doc in docs:
        if doc.get("type") != "table":
            continue
        head = [h.lower() for h in doc["data"]["head"]]
        for row in doc["data"]["body"]:
            cells = dict(zip(head, row))
            yield from from_npm({cells["package"]: cells}, node_modules, skipped)


def from_pip(doc, skipped):
    for row in doc:
        current = version(row.get("version"))
        if not current:
            skipped.append((row.get("name", "?"), "no installed version"))
            continue
        yield dep(row["name"], current, latest=version(row.get("latest_version")), registry="pypi")


def from_go(docs, skipped):
    for row in docs if isinstance(docs, list) else [docs]:
        if row.get("Main"):
            continue
        update = (row.get("Update") or {}).get("Version")
        current = version(row.get("Version"))
        if not update or not current:
            continue
        yield dep(row["Path"], current, latest=update, purl="pkg:golang/" + row["Path"])


def from_cargo(doc, skipped):
    for row in doc["dependencies"]:
        current = version(row.get("project"))
        if not current:
            skipped.append((row.get("name", "?"), "no project version"))
            continue
        yield dep(
            row["name"],
            current,
            version(row.get("compat")),
            version(row.get("latest")),
            registry="crates",
        )


def from_dotnet(doc, skipped):
    seen = set()
    for project in doc.get("projects", []):
        for framework in project.get("frameworks", []):
            for row in framework.get("topLevelPackages", []):
                current = version(row.get("resolvedVersion"))
                if not current or (row["id"], current) in seen:
                    continue
                seen.add((row["id"], current))
                yield dep(
                    row["id"],
                    current,
                    latest=version(row.get("latestVersion")),
                    purl="pkg:nuget/" + row["id"],
                )


def convert(doc, fmt, node_modules=None):
    skipped = []
    fmt = fmt or detect(doc)
    if fmt == "npm":
        deps = list(from_npm(doc, node_modules, skipped))
    elif fmt == "yarn":
        deps = list(from_yarn(doc, node_modules, skipped))
    elif fmt == "pip":
        deps = list(from_pip(doc, skipped))
    elif fmt == "go":
        deps = list(from_go(doc, skipped))
    elif fmt == "cargo":
        deps = list(from_cargo(doc, skipped))
    elif fmt == "dotnet":
        deps = list(from_dotnet(doc, skipped))
    else:
        raise ValueError(f"unknown format {fmt!r}")
    return fmt, deps, skipped


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("report", nargs="?", help="the outdated report (default: stdin)")
    parser.add_argument(
        "--format", choices=["npm", "yarn", "pip", "go", "cargo", "dotnet"], help="skip detection"
    )
    parser.add_argument(
        "--exclude", action="append", default=[], metavar="GLOB",
        help="leave matching package names out (repeatable), e.g. '@acme/*'",
    )
    parser.add_argument(
        "--node-modules", default="node_modules",
        help="where npm packages are installed, for repository and private-registry checks",
    )
    args = parser.parse_args(argv)

    text = open(args.report, encoding="utf-8").read() if args.report else sys.stdin.read()
    node_modules = args.node_modules if os.path.isdir(args.node_modules) else None
    fmt, deps, skipped = convert(load(text), args.format, node_modules)

    kept = []
    for entry in deps:
        if any(fnmatch.fnmatchcase(entry["name"], glob) for glob in args.exclude):
            skipped.append((entry["name"], "excluded"))
        else:
            kept.append(entry)

    for start in range(0, len(kept), BATCH):
        print(json.dumps({"dependencies": kept[start : start + BATCH]}, ensure_ascii=False))

    batches = (len(kept) + BATCH - 1) // BATCH
    print(f"{fmt}: {len(kept)} packages in {batches} batch(es)", file=sys.stderr)
    for name, reason in skipped:
        print(f"  skipped {name}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
