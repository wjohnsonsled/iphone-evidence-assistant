from datetime import datetime,timezone
from uuid import UUID
from app.discovery.apple_backup import *
from app.discovery.metadata_readers import manifest_plist_claims
def u(n):return UUID(f"05030000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def test_manifest_projection_contains_only_owner_approved_encryption_signal():
 observation=MetadataObservation(u(1),u(2),u(3),u(4),u(5),"Manifest.plist","top-level:Manifest.plist","metadata_field","IsEncrypted",ValueState.PRESENT,False,False,"python.plistlib","1",LIMITATIONS)
 result=DiscoveryResult(DISCOVERY_PROFILE_ID,"1",None,(),(observation,),(),EligibilityOutcome.MANIFEST_DB_VALIDATION_PENDING,NOW) # type: ignore[arg-type]
 claims=manifest_plist_claims(result)
 assert claims.profile_id=="manifest-plist-candidate-reader" and claims.profile_version=="1"
 assert claims.observations==(observation,) and claims.observations[0].raw_value is False
 assert tuple(o.field_name for o in claims.observations)==("IsEncrypted",)
