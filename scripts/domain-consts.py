#!/usr/bin/env python3
"""Flag exported consts defined outside a domain folder but used only inside it.

A file belongs to the domain when that name is one of its path components.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

CONST_LINE = re.compile(r"^\s*([A-Z][A-Za-z0-9_]*)\s*=")


def go_files(paths: list[str]) -> list[str]:
    found = []
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix == ".go":
            found.append(path.as_posix())
            continue
        if not path.is_dir():
            continue
        for go in path.rglob("*.go"):
            if "vendor" in go.parts:
                continue
            found.append(go.as_posix())
    return found


def exported_consts(path: Path) -> list[str]:
    names = []
    in_block = False
    for line in path.read_text(errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("const ("):
            in_block = True
            continue
        if in_block and stripped.startswith(")"):
            in_block = False
            continue
        if stripped.startswith("const ") and "(" not in stripped:
            match = CONST_LINE.match(stripped.removeprefix("const "))
            if match:
                names.append(match.group(1))
            continue
        if in_block:
            match = CONST_LINE.match(line)
            if match:
                names.append(match.group(1))
    return names


def in_domain(path: str, domain: str) -> bool:
    return domain in Path(path).parts


def usages(name: str, defined_in: str) -> list[str]:
    proc = subprocess.run(
        ["rg", "-l", "--glob", "*.go", "--glob", "!vendor/**", rf"\b{name}\b", "."],
        text=True,
        capture_output=True,
    )
    if proc.returncode not in (0, 1):
        sys.stderr.write(proc.stderr)
        sys.exit(proc.returncode)
    files = []
    for hit in proc.stdout.splitlines():
        hit = hit.removeprefix("./")
        if hit != defined_in:
            files.append(hit)
    return files


def parse_ignore(items: list[str]) -> set[tuple[str, str]]:
    ignored = set()
    for item in items:
        path, _, name = item.partition(":")
        if not name:
            sys.exit(f"ignore entry must be path:CONST, got {item!r}")
        ignored.add((path, name))
    return ignored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Go files or folders to scan")
    parser.add_argument("--domain", default="network")
    parser.add_argument("--ignore", action="append", default=[], metavar="PATH:CONST")
    args = parser.parse_args()

    ignored = parse_ignore(args.ignore)
    findings = []
    for rel in go_files(args.paths):
        if in_domain(rel, args.domain):
            continue
        for name in exported_consts(Path(rel)):
            if (rel, name) in ignored:
                continue
            hits = usages(name, rel)
            if hits and all(in_domain(hit, args.domain) for hit in hits):
                findings.append((rel, name, hits))

    if not findings:
        print(f"domain-consts: no {args.domain}-only consts defined outside {args.domain}/")
        return 0

    print(f"domain-consts: consts used only under {args.domain}/ but defined elsewhere:")
    for defined_in, name, hits in findings:
        print(f"  {defined_in}: {name}")
        for hit in hits:
            print(f"    {hit}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
