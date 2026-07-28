from importlib.util import module_from_spec,spec_from_file_location
from pathlib import Path
from unittest.mock import patch
M=Path(__file__).parents[1]/"alembic"/"versions"/"0005_processing_idempotency.py"
def load():s=spec_from_file_location("m",M);m=module_from_spec(s);s.loader.exec_module(m);return m
def test_linear_additive_no_seed_migration():
 m=load();assert m.down_revision=="0004_candidate_supported_store"
 with patch.object(m.op,"create_table") as create:m.upgrade()
 assert [c.args[0] for c in create.call_args_list]==["processing_logical_requests","processing_execution_attempts","processing_run_relationships"]
 assert "bulk_insert" not in M.read_text()
def test_reversible_new_tables_only():
 m=load()
 with patch.object(m.op,"drop_table") as drop:m.downgrade()
 assert [c.args[0] for c in drop.call_args_list]==["processing_run_relationships","processing_execution_attempts","processing_logical_requests"]
