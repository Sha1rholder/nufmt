#!/usr/bin/env python3
"""Move temp_tests fixtures into the categories declared in ground_truth.rs."""

import argparse
from collections import Counter
import hashlib
from pathlib import Path
import re
import sys


CATEGORIES = {
    "Core language constructs": "core_language_constructs",
    "Control flow": "control_flow",
    "Data structures": "data_structures",
    "Pipelines, expressions, and operators": "pipelines_expressions_and_operators",
    "Strings, comments, types, and values": "strings_comments_types_and_values",
    "Modules and imports": "modules_and_imports",
    "Commands, definitions, and special constructs": "commands_definitions_and_special_constructs",
    "Ground-truth-only tests (no idempotency pair)": "ground_truth_only",
    "Issue regression tests": "regressions",
}

# This fixture is present on disk but is not registered in ground_truth.rs.
UNREGISTERED_FIXTURES = {"indentation_respects_line_length": "other"}


def fixture_categories(source: Path) -> dict[str, str]:
    text = source.read_text(encoding="utf-8")
    headings = list(re.finditer(r"^// (.+)$", text, re.MULTILINE))
    mapping = {}
    seen_categories = set()
    for index, heading in enumerate(headings):
        category = CATEGORIES.get(heading.group(1))
        if category is None:
            continue
        seen_categories.add(category)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.end():end]
        # Macro tuples and standalone ground-truth calls both name fixtures.
        names = re.findall(
            r'\(\s*"([a-z0-9_]+)"\s*,\s*ground_truth_\w+\s*,\s*idempotency_\w+'
            r'|run_ground_truth_test\(\s*&test_binary\s*,\s*"([a-z0-9_]+)"\s*\)',
            section,
        )
        if not names:
            raise ValueError(f"No fixtures found for category: {category}")
        for paired_name, standalone_name in names:
            name = paired_name or standalone_name
            if name in mapping:
                raise ValueError(f"Fixture appears more than once: {name}")
            mapping[name] = category
    missing = set(CATEGORIES.values()) - seen_categories
    if missing:
        raise ValueError(f"Missing categories in ground_truth.rs: {sorted(missing)}")
    return mapping


def file_hashes(directory: Path) -> dict[str, bytes]:
    entries = list(directory.iterdir())
    if any(not entry.is_file() or entry.is_symlink() for entry in entries):
        raise ValueError(f"Unexpected entry inside test: {directory}")
    names = {entry.name for entry in entries}
    if "expected.nu" not in names or names - {"input.nu", "expected.nu", "config.nuon"}:
        raise ValueError(f"Unexpected fixture files in: {directory}")
    return {
        entry.name: hashlib.sha256(entry.read_bytes()).digest() for entry in entries
    }


def categorize(root: Path, source: Path) -> None:
    mapping = fixture_categories(source)
    for name, category in UNREGISTERED_FIXTURES.items():
        if name not in mapping:
            mapping[name] = category
    temporary = root / "temp_tests"
    if not temporary.is_dir():
        raise ValueError(f"Missing temporary fixture directory: {temporary}")
    tests = sorted(temporary.iterdir())
    if any(not test.is_dir() or test.is_symlink() for test in tests):
        raise ValueError(f"Unexpected non-test entry in: {temporary}")
    actual = {test.name for test in tests}
    if actual != set(mapping):
        raise ValueError(
            f"Fixture/category mismatch: uncategorized={sorted(actual - set(mapping))}, "
            f"missing={sorted(set(mapping) - actual)}"
        )

    moves = []
    for test in tests:
        target = root / mapping[test.name] / test.name
        if target.exists() or target.is_symlink():
            raise ValueError(f"Destination already exists: {target}")
        if target.parent.is_symlink() or (
            target.parent.exists() and not target.parent.is_dir()
        ):
            raise ValueError(f"Invalid category directory: {target.parent}")
        moves.append((test, target, file_hashes(test)))

    for test, target, before in moves:
        target.parent.mkdir(exist_ok=True)
        test.rename(target)
        if file_hashes(target) != before:
            raise ValueError(f"Content changed during move: {target}")
    temporary.rmdir()
    for category, count in sorted(Counter(mapping.values()).items()):
        print(f"{category}: {count}")
    print(f"PASS: categorized {len(tests)} tests; verified all file hashes; removed temp_tests.")


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures-dir", type=Path, default=repository / "tests" / "fixtures")
    parser.add_argument("--ground-truth", type=Path, default=repository / "tests" / "ground_truth.rs")
    args = parser.parse_args()
    try:
        categorize(args.fixtures_dir, args.ground_truth)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
