#!/usr/bin/env python3
"""Call one What's New MCP tool over plain HTTP, for agents with no MCP client.

    python3 whatsnew_call.py upgrade_notes args.json
    python3 whatsnew_call.py missing_changes < args.json

The arguments are the tool's input as one JSON object, from a file or stdin.
Prints the tool's structured result as JSON on stdout. Exit 1 is a transport or
protocol failure; exit 2 is the tool refusing the input (its message on stderr),
which is worth reading and correcting rather than retrying.

The server at https://whatsnew.fyi/mcp is stateless and keyless, so one POST per
call is the whole protocol. Standard library only; Python 3.8+.

This file is copied into every skill that needs it, because a skill installs on
its own. Edit one copy, then copy it over the others; tests/test_scripts.py fails
while they differ.
"""

import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("WHATSNEW_MCP_URL", "https://whatsnew.fyi/mcp")
USER_AGENT = "whatsnew-skills/0.1.0 (+https://github.com/whatsnew-fyi/skills)"
TIMEOUT_SECONDS = 90


def read_args(path):
    raw = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    args = json.loads(raw)
    if not isinstance(args, dict):
        raise ValueError("tool arguments must be one JSON object")
    return args


def parse_body(body, content_type):
    """The reply is plain JSON or SSE-framed JSON (`data: {...}`); both are spec."""
    if "text/event-stream" not in content_type:
        return json.loads(body)
    data = [line[5:].strip() for line in body.splitlines() if line.startswith("data:")]
    if not data:
        raise ValueError("event stream carried no data line")
    return json.loads(data[-1])


def call(tool, args):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args},
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
            "user-agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        body = response.read().decode("utf-8")
        return parse_body(body, response.headers.get("content-type", ""))


def main(argv):
    if len(argv) not in (2, 3) or argv[1] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stderr)
        return 1
    try:
        reply = call(argv[1], read_args(argv[2] if len(argv) == 3 else None))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:500]
        print(f"HTTP {error.code} from {ENDPOINT}: {detail}", file=sys.stderr)
        return 1
    except (urllib.error.URLError, OSError, ValueError) as error:
        print(f"could not call {ENDPOINT}: {error}", file=sys.stderr)
        return 1

    if "error" in reply:
        print(f"protocol error: {json.dumps(reply['error'])}", file=sys.stderr)
        return 1
    result = reply.get("result", {})
    if result.get("isError"):
        text = " ".join(c.get("text", "") for c in result.get("content", []))
        print(text or "the tool refused the input", file=sys.stderr)
        return 2
    structured = result.get("structuredContent")
    if structured is None:
        text = "".join(c.get("text", "") for c in result.get("content", []))
        structured = json.loads(text)
    json.dump(structured, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
