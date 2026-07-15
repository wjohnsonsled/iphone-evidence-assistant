#!/usr/bin/env python3
"""Backward-compatible wrapper for the evidence engine CLI."""

from __future__ import annotations

import sys

from evidence_engine.cli import main


if __name__ == "__main__":
    sys.exit(main())
