from datetime import datetime,timezone
from pathlib import Path
import plistlib
from uuid import UUID
import pytest
from app.discovery.apple_backup import *
def u(n):return UUID(f"05010000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def write(path,value):
 with path.open("wb") as stream:plistlib.dump(value,stream)
def fixture(tmp_path):
 root=tmp_path/"different-directory-name";root.mkdir()
 (root/"Manifest.db").write_bytes(b"SQLite format 3\x00synthetic")
 write(root/"Info.plist",{"Product Version":"17.0","Target Identifier":"DEVICE-A","Unique Identifier":"DEVICE-A"})
 write(root/"Manifest.plist",{"IsEncrypted":False})
 write(root/"Status.plist",{"SnapshotState":"finished"})
 return root
def context(root,**changes):
 values=dict(tenant_id=u(1),case_id=u(2),evidence_source_id=u(3),processing_run_id=u(4),backup_root_artifact_id=u(5),source_artifact_ids={name:u(10+i) for i,name in enumerate(TARGETS)},authorized_root=root.parent,backup_root=root,authorized=True,authorized_scope=(u(1),u(2),u(3)))
 values.update(changes);return DiscoveryContext(**values)
def test_complete_top_level_discovery_is_source_specific_and_pending_validation(tmp_path):
 root=fixture(tmp_path);result=discover(context(root),at=NOW)
 assert [a.source_file for a in result.artifacts]==list(TARGETS)
 assert all(a.state is DiscoveryState.PRESENT_ACCESSIBLE for a in result.artifacts)
 assert result.outcome is EligibilityOutcome.MANIFEST_DB_VALIDATION_PENDING
 assert result.artifacts[1].validation_pending and result.artifacts[1].structurally_recognizable
 assert result.observations[0].observation_type=="BACKUP_ROOT_NAME_OBSERVATION"
 assert {o.source_artifact_id for o in result.observations[1:]}<=set(context(root).source_artifact_ids.values())
@pytest.mark.parametrize("name",TARGETS)
def test_each_required_target_absence_is_explicit_without_deletion_inference(tmp_path,name):
 root=fixture(tmp_path);(root/name).unlink();result=discover(context(root),at=NOW)
 artifact=next(a for a in result.artifacts if a.source_file==name)
 assert artifact.state is DiscoveryState.ABSENT
 assert "deletion" in " ".join(result.limitations).lower()
 assert result.outcome is (EligibilityOutcome.MANIFEST_DB_ABSENT if name=="Manifest.db" else EligibilityOutcome.REQUIRED_METADATA_ABSENT)
def test_inaccessible_and_structurally_invalid_manifest_are_failures(tmp_path):
 root=fixture(tmp_path)
 denied=discover(context(root),at=NOW,header_reader=lambda _:(_ for _ in ()).throw(PermissionError()))
 assert denied.artifacts[1].state is DiscoveryState.PRESENT_INACCESSIBLE and denied.outcome is EligibilityOutcome.MANIFEST_DB_VALIDATION_FAILED
 invalid=discover(context(root),at=NOW,header_reader=lambda _:b"not sqlite")
 assert not invalid.artifacts[1].structurally_recognizable and invalid.outcome is EligibilityOutcome.MANIFEST_DB_VALIDATION_FAILED
def test_malformed_and_unsupported_plist_values_preserve_explicit_states(tmp_path):
 root=fixture(tmp_path);(root/"Info.plist").write_bytes(b"bad")
 malformed=discover(context(root),at=NOW)
 assert any(o.source_file=="Info.plist" and o.value_state is ValueState.MALFORMED for o in malformed.observations)
 write(root/"Info.plist",{"Product Version":{"unsupported":"shape"}})
 unsupported=discover(context(root),at=NOW)
 observation=next(o for o in unsupported.observations if o.field_name=="Product Version")
 assert observation.value_state is ValueState.UNSUPPORTED and observation.raw_value=={"unsupported":"shape"} and observation.normalized_value is None
def test_conflicts_are_unresolved_and_directory_name_is_not_selected(tmp_path):
 root=fixture(tmp_path);write(root/"Info.plist",{"Product Version":"17","Target Identifier":"A","Unique Identifier":"B"})
 result=discover(context(root),at=NOW);device=next(r for r in result.reconciliations if r.field_name=="device_identifier")
 assert device.outcome is ReconciliationOutcome.CONFLICT_UNRESOLVED and device.selected_value is None
 assert device.conflict_category is ConflictCategory.DEVICE_IDENTIFIER_CONFLICT
 assert result.observations[0].raw_value=="different-directory-name"
def test_single_source_missing_and_empty_are_distinct(tmp_path):
 root=fixture(tmp_path);write(root/"Info.plist",{"Product Version":""})
 result=discover(context(root),at=NOW);product=next(o for o in result.observations if o.field_name=="Product Version")
 target=next(o for o in result.observations if o.field_name=="Target Identifier")
 assert product.value_state is ValueState.PRESENT and product.raw_value==""
 assert target.value_state is ValueState.MISSING and target.raw_value is None
 assert next(r for r in result.reconciliations if r.field_name=="product_version").outcome is ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION
def test_encrypted_candidate_is_out_of_scope_without_decryption(tmp_path):
 root=fixture(tmp_path);write(root/"Manifest.plist",{"IsEncrypted":True})
 assert discover(context(root),at=NOW).outcome is EligibilityOutcome.ENCRYPTED_BACKUP_OUT_OF_SCOPE
def test_deterministic_order_profiles_scope_and_root_controls(tmp_path):
 root=fixture(tmp_path);first=discover(context(root),at=NOW);second=discover(context(root),at=NOW)
 assert first==second and first.profile_version=="1" and first.reconciliations[0].profile_version=="1"
 with pytest.raises(ValueError,match="outside"):discover(context(root,authorized_root=tmp_path/"other"),at=NOW)
 with pytest.raises(PermissionError,match="scope"):discover(context(root,authorized_scope=(u(9),u(2),u(3))),at=NOW)
 denied=discover(context(root,authorized=False),at=NOW)
 assert denied.outcome is EligibilityOutcome.DISCOVERY_NOT_AUTHORIZED and denied.artifacts==()
def test_contract_has_no_support_or_user_content_parser_behavior():
 assert set(TARGETS)=={"Manifest.db","Manifest.plist","Info.plist","Status.plist"}
 assert not {"supported","parser_compatible","records_present","device_complete"} & set(DiscoveryResult.__dataclass_fields__)
