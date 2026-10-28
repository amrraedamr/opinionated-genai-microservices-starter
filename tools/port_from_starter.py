"""Port a commit from the single-app starter into this workspace.

The starter keeps everything under `base/`. Here that split in two: shared
infrastructure under `packages/base/base/`, and the parts chat_api owns under
`services/chat_api/chat_api/`. This rewrites a starter patch's paths so it
applies cleanly.

    uv run python tools/port_from_starter.py <sha> [<sha> ...]
    uv run python tools/port_from_starter.py --range upstream/main~3..upstream/main

Paths with no mapping are reported, so a partial port is visible rather than
silent. Pass a stable ref or sha, not FETCH_HEAD: this fetches `upstream`
first and would overwrite it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

BASE = "packages/base/base/"
SERVICE = "services/chat_api/chat_api/"

# Paths chat_api owns. Everything else under base/ is shared infrastructure.
SERVICE_EXACT = {
    "models/definitions/database.py",
    "models/orm/chat_history_message.py",
    "models/orm/conversation.py",
    "models/orm/prompt.py",
    "models/orm/user.py",
    "models/orm/user_identity.py",
    "models/view_models/auth.py",
    "models/view_models/chat.py",
    "models/view_models/conversation.py",
    "models/view_models/user.py",
    "services/agents/test.py",
    "services/auth/__init__.py",
    "services/auth/dependencies.py",
    "services/auth/oauth/__init__.py",
}
SERVICE_PREFIXES = ("routers/", "services/prompt/templates/")

# Renamed during the split.
RENAMES = {"services/store/": "stores/"}

# Restructured beyond a path change; a patch touching these needs a human.
MANUAL = {
    "main.py": "split into packages/base/base/app.py and services/chat_api/chat_api/app.py",
    "services/configuration/settings.py": "split into configuration/core.py and configuration/mixins.py",
    "services/auth/auths.py": "removed; the bearer scheme lives in base/services/auth/bearer.py",
}

DIFF_PATH = re.compile(r"^(diff --git |--- |\+\+\+ |rename from |rename to )(a/|b/)?(.+)$")


def map_path(path: str) -> tuple[str | None, str | None]:
    """Return (new_path, reason) where reason is set only when unmappable."""
    if not path.startswith("base/"):
        return path, None
    rel = path[len("base/") :]
    if rel in MANUAL:
        return None, MANUAL[rel]
    for old, new in RENAMES.items():
        if rel.startswith(old):
            return SERVICE + new + rel[len(old) :], None
    if rel in SERVICE_EXACT or rel.startswith(SERVICE_PREFIXES):
        return SERVICE + rel, None
    return BASE + rel, None


def rewrite(patch: str) -> tuple[str, list[str]]:
    """Rewrite every path in a starter patch. Returns (patch, manual_notes)."""
    out: list[str] = []
    problems: list[str] = []
    for line in patch.splitlines(keepends=True):
        match = DIFF_PATH.match(line.rstrip("\n"))
        if not match:
            out.append(line)
            continue
        head, ab, rest = match.groups()
        if head == "diff --git ":
            parts = rest.split(" b/")
            if len(parts) != 2:
                out.append(line)
                continue
            left = parts[0][2:] if parts[0].startswith("a/") else parts[0]
            new_left, why = map_path(left)
            new_right, _ = map_path(parts[1])
            if why:
                problems.append(f"{left}: {why}")
                out.append(line)
                continue
            out.append(f"diff --git a/{new_left} b/{new_right}\n")
            continue
        if rest == "/dev/null":
            out.append(line)
            continue
        new, why = map_path(rest)
        if why:
            problems.append(f"{rest}: {why}")
            out.append(line)
            continue
        out.append(f"{head}{ab or ''}{new}\n")
    return "".join(out), problems


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed:\n{result.stderr}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("shas", nargs="*", help="starter commits to port")
    parser.add_argument("--range", dest="rev_range", help="a commit range instead")
    parser.add_argument("--check", action="store_true", help="report only, apply nothing")
    parser.add_argument("--no-fetch", action="store_true", help="skip fetching upstream")
    args = parser.parse_args()

    if not args.shas and not args.rev_range:
        parser.error("give at least one sha, or --range")

    if not args.no_fetch:
        git("fetch", "upstream")
    shas = (
        git("rev-list", "--reverse", args.rev_range).split()
        if args.rev_range
        else args.shas
    )

    for sha in shas:
        subject = git("log", "-1", "--format=%s", sha).strip()
        print(f"\n=== {sha[:9]} {subject}")
        rewritten, problems = rewrite(git("format-patch", "-1", "--stdout", sha))

        for problem in problems:
            print(f"  MANUAL: {problem}")

        mode = ["--check"] if args.check else ["--index"]
        applied = subprocess.run(
            ["git", "apply", "--3way", *mode, "-"],
            input=rewritten,
            text=True,
            capture_output=True,
        )
        if applied.returncode != 0:
            print(f"  does not apply cleanly:\n{applied.stderr}")
            return 1
        if args.check:
            print("  applies cleanly")
            continue
        git("commit", "-m", subject, "-m", f"Ported from the starter ({sha[:9]}).")
        print("  applied and committed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
