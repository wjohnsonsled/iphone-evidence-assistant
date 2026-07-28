"""Documented synthetic-only DEV-0209 ceilings."""

from app.intake.resource_limits import IntakeResourcePolicy


TEST_RESOURCE_POLICY = IntakeResourcePolicy(
    max_directory_entries=1_000,
    max_directory_depth=64,
    max_pathname_length=4_096,
    max_plist_bytes=16_777_216,
    max_sqlite_main_bytes=1_073_741_824,
    max_sqlite_wal_bytes=1_073_741_824,
    max_sqlite_shm_bytes=67_108_864,
    max_controlled_copy_bytes=2_214_592_512,
    max_schema_entries=100_000,
    max_sqlite_work_units=100_000_000,
)
