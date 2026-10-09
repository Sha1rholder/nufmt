#!/usr/bin/env python3
"""Delete input.nu when its bytes exactly match the paired expected.nu."""

import argparse
from pathlib import Path
import sys


def remove_identical_inputs(root: Path) -> None:
    if not root.is_dir():
        raise ValueError(f"Missing test directory: {root}")
    tests = sorted(root.iterdir())
    if not tests:
        raise ValueError(f"No tests found in: {root}")

    identical = []
    different = 0
    already_removed = 0
    # Validate and compare every test before deleting any files.
    for test in tests:
        if not test.is_dir():
            raise ValueError(f"Unexpected non-directory entry: {test}")
        expected = test / "expected.nu"
        source = test / "input.nu"
        if not expected.is_file():
            raise ValueError(f"Missing expected file: {expected}")
        if not source.exists():
            already_removed += 1
            continue
        if not source.is_file():
            raise ValueError(f"Input is not a file: {source}")
        if source.read_bytes() == expected.read_bytes():
            identical.append(source)
        else:
            different += 1

    for source in identical:
        source.unlink()
        print(f"Removed: {source.parent.name}/input.nu")
    print(
        f"PASS: checked {len(tests)} tests; removed {len(identical)} identical inputs, "
        f"kept {different} different inputs; {already_removed} inputs already absent."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "temp_tests",
        help="Test directory (default: this repository's tests/fixtures/temp_tests)",
    )
    args = parser.parse_args()
    try:
        remove_identical_inputs(args.tests_dir)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
