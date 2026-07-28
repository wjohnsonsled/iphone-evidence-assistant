"""Backend test configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("EVIDENCE_ROOT", str(ROOT / "fixtures"))
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("INTAKE_MAX_DIRECTORY_ENTRIES", "1000")
os.environ.setdefault("INTAKE_MAX_DIRECTORY_DEPTH", "64")
os.environ.setdefault("INTAKE_MAX_PATHNAME_LENGTH", "4096")
os.environ.setdefault("INTAKE_MAX_PLIST_BYTES", "16777216")
os.environ.setdefault("INTAKE_MAX_SQLITE_MAIN_BYTES", "1073741824")
os.environ.setdefault("INTAKE_MAX_SQLITE_WAL_BYTES", "1073741824")
os.environ.setdefault("INTAKE_MAX_SQLITE_SHM_BYTES", "67108864")
os.environ.setdefault("INTAKE_MAX_CONTROLLED_COPY_BYTES", "2214592512")
os.environ.setdefault("INTAKE_MAX_SCHEMA_ENTRIES", "100000")
os.environ.setdefault("INTAKE_MAX_SQLITE_WORK_UNITS", "100000000")
