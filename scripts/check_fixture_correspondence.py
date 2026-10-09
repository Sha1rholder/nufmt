#!/usr/bin/env python3
"""Check input/expected filenames and config-to-input fixture correspondence."""

import argparse
from pathlib import Path
import sys


def fixture_files(directory: Path) -> set[str]:
    if not directory.is_dir():
        raise ValueError(f"Missing fixture directory: {directory}")
    entries = list(directory.iterdir())
    non_files = sorted(entry.name for entry in entries if not entry.is_file())
    if non_files:
        raise ValueError(f"Unexpected non-file entries in {directory}: {non_files}")
    return {entry.name for entry in entries}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tests" / "fixtures",
        help="Fixture root (default: this repository's tests/fixtures)",
    )
    args = parser.parse_args()
    try:
        inputs = fixture_files(args.fixtures_dir / "input")
        expected = fixture_files(args.fixtures_dir / "expected")
        configs = fixture_files(args.fixtures_dir / "config")
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    input_stems = {Path(name).stem for name in inputs}
    failures = {
        "Input files without an expected file": inputs - expected,
        "Expected files without an input file": expected - inputs,
        "Config files without an input file of the same stem": {
            name for name in configs if Path(name).stem not in input_stems
        },
    }
    print(f"Files: input={len(inputs)}, expected={len(expected)}, config={len(configs)}")
    for description, names in failures.items():
        if names:
            print(f"{description}:")
            for name in sorted(names):
                print(f"  {name}")
    if any(failures.values()):
        print("FAIL: fixture correspondence check failed.")
        return 1
    print("PASS: input/expected filenames match; every config has a matching input stem.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
