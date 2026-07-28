from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
from unittest.mock import patch
M=Path(__file__).parents[1]/"alembic"/"versions"/"0004_candidate_supported_store.py"
def load():
 s=spec_from_file_location("m",M);m=module_from_spec(s);s.loader.exec_module(m);return m
def test_linear_additive_migration_and_no_seed_operations():
 m=load();assert m.down_revision=="0003_security_foundation"
 with patch.object(m.op,"create_table") as create:
  m.upgrade()
 names=[c.args[0] for c in create.call_args_list]
 assert "supported_normalized_records" in names and "supported_admission_decisions" in names
 assert "bulk_insert" not in M.read_text()
def test_downgrade_removes_only_new_tables():
 m=load()
 with patch.object(m.op,"drop_table") as drop:m.downgrade()
 assert drop.call_args_list[-1].args[0]=="supported_processing_runs"
