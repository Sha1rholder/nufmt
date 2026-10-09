#!/usr/bin/env python3
"""Move flat fixtures into temp_tests/<test name>/ and verify their bytes."""

import argparse
import hashlib
from pathlib import Path
import sys

from check_fixture_correspondence import fixture_files


def digest(path: Path) -> bytes:
    return hashlib.sha256(path.read_bytes()).digest()


def group_fixtures(root: Path) -> None:
    inputs = fixture_files(root / "input")
    expected = fixture_files(root / "expected")
    configs = fixture_files(root / "config")
    if not inputs or inputs != expected:
        raise ValueError("Input/expected must be nonempty and have identical filenames")
    if any(Path(name).suffix != ".nu" for name in inputs):
        raise ValueError("All input/expected files must have the .nu suffix")
    if any(Path(name).suffix != ".nuon" for name in configs):
        raise ValueError("All config files must have the .nuon suffix")
    stems = {Path(name).stem for name in inputs}
    if any(Path(name).stem not in stems for name in configs):
        raise ValueError("Every config must have an input with the same stem")

    destination = root / "temp_tests"
    if destination.exists() and (
        not destination.is_dir() or any(destination.iterdir())
    ):
        raise ValueError(f"Destination must be absent or empty: {destination}")

    moves = []
    for source_dir, names, target_name in (
        ("input", inputs, "input.nu"),
        ("expected", expected, "expected.nu"),
        ("config", configs, "config.nuon"),
    ):
        for name in sorted(names):
            source = root / source_dir / name
            target = destination / Path(name).stem / target_name
            moves.append((source, target, digest(source)))

    destination.mkdir(exist_ok=True)
    for stem in sorted(stems):
        (destination / stem).mkdir()
    for source, target, before in moves:
        source.rename(target)
        if digest(target) != before:
            raise ValueError(f"Content changed during move: {target}")

    for source_dir in ("input", "expected", "config"):
        if any((root / source_dir).iterdir()):
            raise ValueError(f"Source directory is not empty: {source_dir}")
    print(
        f"PASS: grouped {len(stems)} tests; moved {len(inputs)} input, "
        f"{len(expected)} expected, and {len(configs)} config files."
    )
    print(f"Verified SHA-256 hashes for all {len(moves)} moved files.")


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
        group_fixtures(args.fixtures_dir)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
