from datetime import datetime,timezone
from uuid import UUID
from app.discovery.apple_backup import *
from app.discovery.metadata_readers import status_plist_claims
def u(n):return UUID(f"05040000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def test_status_projection_is_snapshot_claim_not_completeness_conclusion():
 observation=MetadataObservation(u(1),u(2),u(3),u(4),u(5),"Status.plist","top-level:Status.plist","metadata_field","SnapshotState",ValueState.PRESENT,"finished","finished","python.plistlib","1",LIMITATIONS)
 result=DiscoveryResult(DISCOVERY_PROFILE_ID,"1",None,(),(observation,),(),EligibilityOutcome.MANIFEST_DB_VALIDATION_PENDING,NOW) # type: ignore[arg-type]
 claims=status_plist_claims(result)
 assert claims.profile_id=="status-plist-candidate-reader" and claims.observations==(observation,)
 assert claims.observations[0].normalized_value=="finished"
 assert not {"backup_complete","forensically_complete","supported"} & set(claims.__dataclass_fields__)
