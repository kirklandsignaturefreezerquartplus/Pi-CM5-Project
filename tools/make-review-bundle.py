#!/usr/bin/env python3
"""Bundle every tracked file of the project into one Markdown file for review.

    tools/make-review-bundle.py            # (re)writes REVIEW_BUNDLE.md
    tools/make-review-bundle.py --check    # verifies the bundle matches the tree

The bundle is a convenience for code review and portability only; nothing
runs from it.  Each file appears under a heading with its size, line count
and SHA-256, inside a fenced block whose fence is longer than any run of
backticks in the file, so Markdown documents that themselves contain code
fences render correctly.  ``--check`` parses the bundle back into files and
compares every one byte for byte with the working tree, and fails if a
tracked file is missing from the bundle or the bundle contains a file that
is no longer tracked.
"""
from __future__ import annotations

import datetime
import hashlib
import os
import re
import subprocess
import sys

BUNDLE_NAME = "REVIEW_BUNDLE.md"

# Presentation order: reading order for a reviewer.
ORDER = [
    "README.md",
    "docs/GUIDE.md",
    "docs/hardware.md",
    "docs/pikvm.md",
    "docs/usb-identity.md",
    "docs/remaining-tells.md",
    "docs/review-analysis.md",
    "docs/macros.md",
    "docs/troubleshooting.md",
    "config/config.toml",
    "hid_bridge/__init__.py",
    "hid_bridge/__main__.py",
    "hid_bridge/config.py",
    "hid_bridge/descriptors.py",
    "hid_bridge/keymap.py",
    "hid_bridge/reports.py",
    "hid_bridge/linux_input.py",
    "hid_bridge/hidg.py",
    "hid_bridge/gadget.py",
    "hid_bridge/macros.py",
    "hid_bridge/control.py",
    "hid_bridge/bridge.py",
    "tests/",
    "tools/",
    "bin/hid-bridge",
    "systemd/",
    "install.sh",
    "uninstall.sh",
    "Makefile",
    ".gitignore",
    "kernel-patches/README.md",
    "kernel-patches/",
]

LANGUAGES = {
    ".py": "python", ".md": "markdown", ".toml": "toml", ".sh": "bash",
    ".service": "ini", ".patch": "diff", ".ps1": "powershell", ".txt": "text",
}


def repo_root() -> str:
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True)
    return out.stdout.strip()


def tracked_files(root: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=root, capture_output=True, check=True)
    files = [f for f in out.stdout.decode().split("\0") if f]
    return [f for f in files if f != BUNDLE_NAME and os.path.isfile(os.path.join(root, f))]


def ordered(files: list[str]) -> list[str]:
    remaining = sorted(files)
    result: list[str] = []
    for key in ORDER:
        if key.endswith("/"):
            group = [f for f in remaining if f.startswith(key)]
        else:
            group = [f for f in remaining if f == key]
        for f in group:
            result.append(f)
            remaining.remove(f)
    return result + remaining


def language_for(path: str) -> str:
    base = os.path.basename(path)
    if base == "Makefile":
        return "makefile"
    if base == "hid-bridge" or base.endswith(".sh"):
        return "bash"
    if base == ".gitignore":
        return "text"
    return LANGUAGES.get(os.path.splitext(base)[1], "text")


def anchor_for(path: str) -> str:
    """GitHub-style heading anchor for ``## <path>``."""
    text = path.lower()
    text = re.sub(r"[^a-z0-9 _-]", "", text)
    return text.replace(" ", "-")


def fence_for(text: str) -> str:
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def git_describe(root: str) -> tuple[str, str]:
    def run(*args: str) -> str:
        try:
            return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"
    return run("rev-parse", "--short", "HEAD"), run("rev-parse", "--abbrev-ref", "HEAD")


def build(root: str) -> str:
    files = ordered(tracked_files(root))
    commit, branch = git_describe(root)
    total = 0
    sections: list[str] = []
    toc: list[str] = []
    for index, path in enumerate(files, 1):
        with open(os.path.join(root, path), "rb") as fh:
            raw = fh.read()
        total += len(raw)
        text = raw.decode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        lines = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
        trailing = "" if text.endswith("\n") or not text else " (no trailing newline)"
        fence = fence_for(text)
        body = text if (text.endswith("\n") or not text) else text + "\n"
        toc.append(f"{index}. [{path}](#{anchor_for(path)})")
        sections.append(
            f"## {path}\n\n"
            f"`{len(raw)} bytes, {lines} lines, sha256 {digest}`{trailing}\n\n"
            f"{fence}{language_for(path)}\n{body}{fence}\n"
        )
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        "# hid-bridge: review bundle\n\n"
        "Every tracked file of the project in one document, for code review and\n"
        "portability only.  Nothing runs from this file; install from the\n"
        "repository.  Regenerate with `tools/make-review-bundle.py` (or `make\n"
        "bundle`) and verify with `tools/make-review-bundle.py --check`.\n\n"
        f"* Generated: {now}\n"
        f"* Base commit: `{commit}` on `{branch}` (built from the working tree, so the\n"
        "  content may be ahead of that commit; `--check` compares against the tree)\n"
        f"* Files: {len(files)} ({total:,} bytes)\n\n"
        "## Contents\n\n" + "\n".join(toc) + "\n\n"
    )
    return header + "\n".join(sections)


SECTION_RE = re.compile(
    r"^## (?P<path>\S+)\n\n`(?P<bytes>\d+) bytes, (?P<lines>\d+) lines, sha256 (?P<sha>[0-9a-f]{64})`"
    r"(?P<trailing> \(no trailing newline\))?\n\n(?P<fence>`{3,})(?P<lang>[a-z]*)\n",
    re.M,
)


def parse(bundle: str) -> dict[str, bytes]:
    """Recover {path: content} from a bundle; raises ValueError on malformed sections."""
    files: dict[str, bytes] = {}
    pos = 0
    while True:
        match = SECTION_RE.search(bundle, pos)
        if not match:
            break
        fence = match.group("fence")
        start = match.end()
        end = bundle.find("\n" + fence + "\n", start - 1)
        if end < 0:
            raise ValueError(f"unterminated section for {match.group('path')}")
        body = bundle[start:end + 1]
        if match.group("trailing"):
            body = body[:-1]
        content = body.encode("utf-8")
        if hashlib.sha256(content).hexdigest() != match.group("sha"):
            raise ValueError(f"checksum mismatch inside the bundle for {match.group('path')}")
        files[match.group("path")] = content
        pos = end + len(fence) + 2
    return files


def check(root: str) -> int:
    bundle_path = os.path.join(root, BUNDLE_NAME)
    try:
        with open(bundle_path, encoding="utf-8") as fh:
            bundled = parse(fh.read())
    except FileNotFoundError:
        print(f"{BUNDLE_NAME} does not exist; run tools/make-review-bundle.py", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"{BUNDLE_NAME} is malformed: {exc}", file=sys.stderr)
        return 1
    tracked = set(tracked_files(root))
    problems = []
    for path in sorted(tracked - set(bundled)):
        problems.append(f"missing from bundle: {path}")
    for path in sorted(set(bundled) - tracked):
        problems.append(f"in bundle but not tracked: {path}")
    for path in sorted(tracked & set(bundled)):
        with open(os.path.join(root, path), "rb") as fh:
            if fh.read() != bundled[path]:
                problems.append(f"differs from working tree: {path}")
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        print(f"{BUNDLE_NAME} is stale: regenerate with tools/make-review-bundle.py", file=sys.stderr)
        return 1
    print(f"{BUNDLE_NAME}: {len(bundled)} files, all identical to the working tree")
    return 0


def main(argv: list[str]) -> int:
    root = repo_root()
    if argv[1:] == ["--check"]:
        return check(root)
    if argv[1:]:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    bundle = build(root)
    with open(os.path.join(root, BUNDLE_NAME), "w", encoding="utf-8") as fh:
        fh.write(bundle)
    print(f"wrote {BUNDLE_NAME} ({len(bundle.encode()):,} bytes)")
    return check(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
