from datetime import datetime, timezone
from uuid import UUID
import pytest
from app.evidence_core.schema_fingerprint import record_schema_fingerprint
def u(n: int) -> UUID: return UUID(f"45000000-0000-4000-8000-{n:012d}")
BASE = dict(source_artifact_id=u(1), processing_run_id=u(2), parser_identity_id=None,
 profile_id="manifest-db-dec-0008-candidate", profile_version="1",
 canonical_input_reference="FOR-007 section 13", sha256_digest="ab"*32,
 observed_at=datetime(2026,7,28,tzinfo=timezone.utc),
 limitations=("Observation only; no compatibility or support conclusion.",))
def test_qualified_observation():
    item=record_schema_fingerprint(**BASE)
    assert item.observation_id.version == 4 and item.parser_identity_id is None
@pytest.mark.parametrize("change",[{"profile_id":"Universal Schema"},{"sha256_digest":"AB"*32},{"sha256_digest":"ab"},{"limitations":()},{"observed_at":datetime(2026,7,28)}])
def test_invalid_observation(change):
    with pytest.raises(ValueError): record_schema_fingerprint(**(BASE|change))
def test_no_conclusion_fields():
    fields=set(record_schema_fingerprint(**BASE).__dataclass_fields__)
    assert not {"compatible","schema_equivalent","parse_success","support_status","apple_compatible"} & fields
