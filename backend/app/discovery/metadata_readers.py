"""Versioned projections over DEV-0501 source-specific plist observations."""
from dataclasses import dataclass
from app.discovery.apple_backup import DiscoveryResult,MetadataObservation,ReconciliationResult
@dataclass(frozen=True,slots=True)
class MetadataClaimSet:
 profile_id:str;profile_version:str;source_file:str;observations:tuple[MetadataObservation,...];limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class ReconciledClaimSet:
 profile_id:str;profile_version:str;results:tuple[ReconciliationResult,...];limitations:tuple[str,...]
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
def encryption_version_reconciliation(result:DiscoveryResult)->ReconciledClaimSet:
 selected=tuple(item for item in result.reconciliations if item.field_name in {"encryption","product_version"})
 if tuple(item.field_name for item in selected)!=("product_version","encryption"):raise ValueError("reconciliation_claim_set_incomplete")
 return ReconciledClaimSet("encryption-version-exact-reconciliation","1",selected,result.limitations)
