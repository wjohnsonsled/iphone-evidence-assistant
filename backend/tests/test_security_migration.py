from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest.mock import call, patch


MIGRATION = (
    Path(__file__).parents[1]
    / "alembic"
    / "versions"
    / "0003_security_foundation.py"
)


def _load_migration():
    spec = spec_from_file_location("security_migration", MIGRATION)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_security_migration_is_linear_and_additive() -> None:
    migration = _load_migration()
    assert migration.revision == "0003_security_foundation"
    assert migration.down_revision == "0002_evidence_integrity"

    with patch.object(migration.op, "create_table") as create_table, patch.object(
        migration.op, "create_index"
    ):
        migration.upgrade()

    assert [item.args[0] for item in create_table.call_args_list] == [
        "security_tenants",
        "security_principals",
        "security_tenant_memberships",
        "security_cases",
        "security_evidence_sources",
    ]


def test_security_migration_downgrade_removes_only_new_tables_in_reverse_order() -> None:
    migration = _load_migration()
    with patch.object(migration.op, "drop_table") as drop_table:
        migration.downgrade()
    assert drop_table.call_args_list == [
        call("security_evidence_sources"),
        call("security_cases"),
        call("security_tenant_memberships"),
        call("security_principals"),
        call("security_tenants"),
    ]
