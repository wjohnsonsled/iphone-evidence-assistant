"""Versioned projections over DEV-0501 source-specific plist observations."""
from dataclasses import dataclass
from app.discovery.apple_backup import DiscoveryResult,MetadataObservation
@dataclass(frozen=True,slots=True)
class MetadataClaimSet:
 profile_id:str;profile_version:str;source_file:str;observations:tuple[MetadataObservation,...];limitations:tuple[str,...]
def _claims(result,source,fields,profile):
 if result.profile_id!="apple-local-backup-top-level-discovery":raise ValueError("discovery_profile_mismatch")
 observations=tuple(o for o in result.observations if o.source_file==source and o.field_name in fields)
 if tuple(o.field_name for o in observations)!=fields:raise ValueError("metadata_claim_set_incomplete")
 return MetadataClaimSet(profile,"1",source,observations,result.limitations)
def info_plist_claims(result:DiscoveryResult)->MetadataClaimSet:
 return _claims(result,"Info.plist",("Product Version","Target Identifier","Unique Identifier"),"info-plist-candidate-reader")
def manifest_plist_claims(result:DiscoveryResult)->MetadataClaimSet:
 return _claims(result,"Manifest.plist",("IsEncrypted",),"manifest-plist-candidate-reader")
def status_plist_claims(result:DiscoveryResult)->MetadataClaimSet:
 return _claims(result,"Status.plist",("SnapshotState",),"status-plist-candidate-reader")
