"""System file and plist parser implementations."""

from evidence_engine._legacy import (
    PlistSystemPlugin,
    SystemFilePlugin,
    classify_system_source,
    summarize_plist,
)

__all__ = [
    "PlistSystemPlugin",
    "SystemFilePlugin",
    "classify_system_source",
    "summarize_plist",
]
