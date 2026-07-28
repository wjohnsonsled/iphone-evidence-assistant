from datetime import datetime,timezone
from pathlib import Path
import plistlib
from uuid import UUID
import pytest
from app.discovery.apple_backup import *
from app.discovery.metadata_readers import info_plist_claims
def u(n):return UUID(f"05020000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def test_info_projection_is_complete_ordered_source_specific_and_versioned(tmp_path):
 root=tmp_path/"backup";root.mkdir();(root/"Manifest.db").write_bytes(b"SQLite format 3\x00")
 for name,value in (("Info.plist",{"Product Version":"17","Target Identifier":"","Unique Identifier":"U"}),("Manifest.plist",{"IsEncrypted":False}),("Status.plist",{"SnapshotState":"finished"})):
  with (root/name).open("wb") as stream:plistlib.dump(value,stream)
 context=DiscoveryContext(u(1),u(2),u(3),u(4),u(5),{n:u(10+i) for i,n in enumerate(TARGETS)},tmp_path,root,True,(u(1),u(2),u(3)))
 claims=info_plist_claims(discover(context,at=NOW))
 assert claims.profile_id=="info-plist-candidate-reader" and claims.profile_version=="1"
 assert tuple(o.field_name for o in claims.observations)==("Product Version","Target Identifier","Unique Identifier")
 assert claims.observations[1].raw_value=="" and all(o.source_file=="Info.plist" for o in claims.observations)
def test_projection_rejects_incomplete_or_wrong_profile():
 result=DiscoveryResult("wrong","1",None,(),(),(),EligibilityOutcome.DISCOVERY_FAILED,NOW) # type: ignore[arg-type]
 with pytest.raises(ValueError,match="profile"):info_plist_claims(result)
