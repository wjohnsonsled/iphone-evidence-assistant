"""Validate the repository dependency lock without network access."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

PIN = re.compile(r"^([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)$")
NAME = re.compile(r"^([A-Za-z0-9_.-]+)")


def normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def validate(project_file: Path, lock_file: Path) -> list[str]:
    errors: list[str] = []
    project = tomllib.loads(project_file.read_text(encoding="utf-8"))
    declared = (
        project["project"]["dependencies"]
        + project["project"]["optional-dependencies"]["dev"]
        + project.get("build-system", {}).get("requires", [])
    )
    required = {normalized(NAME.match(item).group(1)) for item in declared}
    pins: dict[str, str] = {}
    for number, raw_line in enumerate(lock_file.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = PIN.fullmatch(line)
        if match is None:
            errors.append(f"line {number}: dependency is not an exact name==version pin")
            continue
        name, version = normalized(match.group(1)), match.group(2)
        if name in pins:
            errors.append(f"line {number}: duplicate dependency {name}")
        pins[name] = version
    missing = sorted(required - pins.keys())
    if missing:
        errors.append("direct dependencies absent from lock: " + ", ".join(missing))
    if not pins:
        errors.append("lock contains no dependency pins")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path("pyproject.toml"))
    parser.add_argument("--lock", type=Path, default=Path("requirements.lock"))
    arguments = parser.parse_args()
    errors = validate(arguments.project, arguments.lock)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"lock valid: {arguments.lock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
