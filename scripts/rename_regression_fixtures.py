#!/usr/bin/env python3
"""Rename regression directories from <name>_issue<number> to <number>_<name>."""

import argparse
import hashlib
from pathlib import Path
import re
import sys


def file_hashes(directory: Path) -> dict[str, bytes]:
    entries = list(directory.iterdir())
    if any(not entry.is_file() or entry.is_symlink() for entry in entries):
        raise ValueError(f"Unexpected entry inside test: {directory}")
    return {
        entry.name: hashlib.sha256(entry.read_bytes()).digest() for entry in entries
    }


def rename_regressions(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"Missing or invalid regression directory: {root}")
    tests = sorted(root.iterdir())
    if not tests:
        raise ValueError(f"No regression tests found in: {root}")

    moves = []
    targets = set()
    # Check every destination and read all contents before renaming anything.
    for test in tests:
        if not test.is_dir() or test.is_symlink():
            raise ValueError(f"Unexpected non-test entry: {test}")
        match = re.fullmatch(r"(.+)_issue([0-9]+)", test.name)
        if match is None:
            continue
        name, issue = match.groups()
        target = root / f"{issue}_{name}"
        if target.exists() or target.is_symlink() or target in targets:
            raise ValueError(f"Destination already exists or is duplicated: {target}")
        targets.add(target)
        moves.append((test, target, file_hashes(test)))

    for test, target, before in moves:
        test.rename(target)
        if file_hashes(target) != before:
            raise ValueError(f"Content changed during rename: {target}")

    print(
        f"PASS: renamed {len(moves)} regression directories; "
        f"kept {len(tests) - len(moves)} names without an _issue<number> suffix."
    )
    print("Verified SHA-256 hashes for all files in renamed directories.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--regressions-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "regressions",
        help="Regression directory (default: this repository's tests/fixtures/regressions)",
    )
    args = parser.parse_args()
    try:
        rename_regressions(args.regressions_dir)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
