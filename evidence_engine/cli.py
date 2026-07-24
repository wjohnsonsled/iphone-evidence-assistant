"""Command-line entry point for the evidence engine."""

from __future__ import annotations

from collections.abc import Sequence

from evidence_engine._legacy import build_arg_parser, main as _legacy_main


def main(argv: Sequence[str] | None = None) -> int:
    """Run the backward-compatible window investigator command."""

    return _legacy_main(argv)


__all__ = ["build_arg_parser", "main"]


if __name__ == "__main__":
    raise SystemExit(main())
