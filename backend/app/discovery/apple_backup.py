"""Root-confined Apple backup metadata discovery and reconciliation."""
from __future__ import annotations
import plistlib,stat
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any,Callable
from uuid import UUID

DISCOVERY_PROFILE_ID="apple-local-backup-top-level-discovery";DISCOVERY_PROFILE_VERSION="1"
RECONCILIATION_PROFILE_ID="apple-backup-metadata-field-reconciliation";RECONCILIATION_PROFILE_VERSION="1"
TARGETS=("Info.plist","Manifest.db","Manifest.plist","Status.plist")
FIELDS={"Info.plist":("Product Version","Target Identifier","Unique Identifier"),"Manifest.plist":("IsEncrypted",),"Status.plist":("SnapshotState",)}
LIMITATIONS=("Discovery is limited to authorized expected top-level locations.","Absence does not prove deletion, concealment, destruction, or evidentiary absence.","Discovery does not establish forensic completeness, Apple compatibility, parser support, or artifact support.")
class DiscoveryState(str,Enum):
 PRESENT_ACCESSIBLE="PRESENT_ACCESSIBLE";PRESENT_INACCESSIBLE="PRESENT_INACCESSIBLE";PRESENT_INVALID_TYPE="PRESENT_INVALID_TYPE";ABSENT="ABSENT";DISCOVERY_NOT_AUTHORIZED="DISCOVERY_NOT_AUTHORIZED";DISCOVERY_NOT_EXECUTED="DISCOVERY_NOT_EXECUTED";DISCOVERY_FAILED="DISCOVERY_FAILED";INDETERMINATE="INDETERMINATE"
class EligibilityOutcome(str,Enum):
 DISCOVERY_COMPLETE="DISCOVERY_COMPLETE";DISCOVERY_COMPLETE_WITH_CONFLICTS="DISCOVERY_COMPLETE_WITH_CONFLICTS";DISCOVERY_COMPLETE_WITH_LIMITATIONS="DISCOVERY_COMPLETE_WITH_LIMITATIONS";DISCOVERY_ZERO_OPTIONAL_METADATA="DISCOVERY_ZERO_OPTIONAL_METADATA";REQUIRED_METADATA_ABSENT="REQUIRED_METADATA_ABSENT";MANIFEST_DB_ABSENT="MANIFEST_DB_ABSENT";MANIFEST_DB_VALIDATION_PENDING="MANIFEST_DB_VALIDATION_PENDING";MANIFEST_DB_VALIDATION_FAILED="MANIFEST_DB_VALIDATION_FAILED";ENCRYPTED_BACKUP_OUT_OF_SCOPE="ENCRYPTED_BACKUP_OUT_OF_SCOPE";STRUCTURE_VALIDATION_REQUIRED="STRUCTURE_VALIDATION_REQUIRED";STRUCTURE_NOT_RECOGNIZED="STRUCTURE_NOT_RECOGNIZED";DISCOVERY_NOT_AUTHORIZED="DISCOVERY_NOT_AUTHORIZED";DISCOVERY_FAILED="DISCOVERY_FAILED";DISCOVERY_INDETERMINATE="DISCOVERY_INDETERMINATE"
class ValueState(str,Enum):PRESENT="PRESENT";MISSING="MISSING";MALFORMED="MALFORMED";UNSUPPORTED="UNSUPPORTED"
class ReconciliationOutcome(str,Enum):
 AGREEMENT="AGREEMENT";SINGLE_SOURCE_OBSERVATION="SINGLE_SOURCE_OBSERVATION";CONFLICT_RESOLVED_BY_GOVERNED_RULE="CONFLICT_RESOLVED_BY_GOVERNED_RULE";CONFLICT_UNRESOLVED="CONFLICT_UNRESOLVED";VALUE_MISSING_FROM_ALL_SOURCES="VALUE_MISSING_FROM_ALL_SOURCES";SOURCE_UNAVAILABLE="SOURCE_UNAVAILABLE";INTERPRETATION_UNSUPPORTED="INTERPRETATION_UNSUPPORTED";INDETERMINATE="INDETERMINATE"
class ConflictCategory(str,Enum):
 DEVICE_IDENTIFIER_CONFLICT="DEVICE_IDENTIFIER_CONFLICT";PRODUCT_VERSION_CONFLICT="PRODUCT_VERSION_CONFLICT";BACKUP_IDENTIFIER_CONFLICT="BACKUP_IDENTIFIER_CONFLICT";ENCRYPTION_INDICATOR_CONFLICT="ENCRYPTION_INDICATOR_CONFLICT";SNAPSHOT_STATE_CONFLICT="SNAPSHOT_STATE_CONFLICT";BACKUP_TIME_CONFLICT="BACKUP_TIME_CONFLICT";SOURCE_METADATA_CONFLICT="SOURCE_METADATA_CONFLICT";UNKNOWN_METADATA_CONFLICT="UNKNOWN_METADATA_CONFLICT"
@dataclass(frozen=True,slots=True)
class DiscoveryContext:
 tenant_id:UUID;case_id:UUID;evidence_source_id:UUID;processing_run_id:UUID;backup_root_artifact_id:UUID;source_artifact_ids:dict[str,UUID];authorized_root:Path;backup_root:Path;authorized:bool;authorized_scope:tuple[UUID,UUID,UUID]
@dataclass(frozen=True,slots=True)
class MetadataObservation:
 tenant_id:UUID;case_id:UUID;evidence_source_id:UUID;source_artifact_id:UUID;processing_run_id:UUID;source_file:str;source_locator:str;observation_type:str;field_name:str|None;value_state:ValueState;raw_value:Any;normalized_value:Any;reader_id:str;reader_version:str;limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class ArtifactDiscovery:
 source_file:str;source_artifact_id:UUID;state:DiscoveryState;structurally_recognizable:bool|None;validation_pending:bool;failure_code:str|None
@dataclass(frozen=True,slots=True)
class ReconciliationResult:
 profile_id:str;profile_version:str;field_name:str;observation_indexes:tuple[int,...];outcome:ReconciliationOutcome;selected_value:Any;basis:str|None;conflict_category:ConflictCategory|None;reconciled_at:datetime;limitations:tuple[str,...]
@dataclass(frozen=True,slots=True)
class DiscoveryResult:
 profile_id:str;profile_version:str;context:DiscoveryContext;artifacts:tuple[ArtifactDiscovery,...];observations:tuple[MetadataObservation,...];reconciliations:tuple[ReconciliationResult,...];outcome:EligibilityOutcome;discovered_at:datetime;limitations:tuple[str,...]=LIMITATIONS
def reconcile(field,observations,indexes,*,at):
 selected=[observations[i] for i in indexes if observations[i].value_state is ValueState.PRESENT]
 if not selected:return ReconciliationResult(RECONCILIATION_PROFILE_ID,RECONCILIATION_PROFILE_VERSION,field,tuple(indexes),ReconciliationOutcome.VALUE_MISSING_FROM_ALL_SOURCES,None,None,None,at,LIMITATIONS)
 values={repr(item.normalized_value) for item in selected}
 if len(selected)==1:outcome=ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION
 elif len(values)==1:outcome=ReconciliationOutcome.AGREEMENT
 else:outcome=ReconciliationOutcome.CONFLICT_UNRESOLVED
 category={"device_identifier":ConflictCategory.DEVICE_IDENTIFIER_CONFLICT,"product_version":ConflictCategory.PRODUCT_VERSION_CONFLICT,"backup_identifier":ConflictCategory.BACKUP_IDENTIFIER_CONFLICT,"encryption":ConflictCategory.ENCRYPTION_INDICATOR_CONFLICT,"snapshot_state":ConflictCategory.SNAPSHOT_STATE_CONFLICT}.get(field,ConflictCategory.SOURCE_METADATA_CONFLICT) if outcome is ReconciliationOutcome.CONFLICT_UNRESOLVED else None
 value=selected[0].normalized_value if outcome is not ReconciliationOutcome.CONFLICT_UNRESOLVED else None
 return ReconciliationResult(RECONCILIATION_PROFILE_ID,RECONCILIATION_PROFILE_VERSION,field,tuple(indexes),outcome,value,"exact_value_agreement" if outcome is ReconciliationOutcome.AGREEMENT else ("single_source_only" if outcome is ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION else None),category,at,LIMITATIONS)
def discover(context:DiscoveryContext,*,at:datetime,plist_reader:Callable[[Path],Any]|None=None,header_reader:Callable[[Path],bytes]|None=None)->DiscoveryResult:
 if at.tzinfo is None:raise ValueError("discovery_time_required")
 if not context.authorized:return DiscoveryResult(DISCOVERY_PROFILE_ID,DISCOVERY_PROFILE_VERSION,context,(),(),(),EligibilityOutcome.DISCOVERY_NOT_AUTHORIZED,at)
 if (context.tenant_id,context.case_id,context.evidence_source_id)!=context.authorized_scope:raise PermissionError("discovery_scope_mismatch")
 root=context.backup_root.resolve();authorized=context.authorized_root.resolve()
 if root!=authorized and authorized not in root.parents:raise ValueError("backup_root_outside_authorized_root")
 if set(context.source_artifact_ids)!=set(TARGETS):raise ValueError("source_artifact_scope_incomplete")
 read_plist=plist_reader or (lambda path:plistlib.load(path.open("rb")))
 read_header=header_reader or (lambda path:path.open("rb").read(16))
 artifacts=[];observations=[MetadataObservation(context.tenant_id,context.case_id,context.evidence_source_id,context.backup_root_artifact_id,context.processing_run_id,".","backup-root:name","BACKUP_ROOT_NAME_OBSERVATION",None,ValueState.PRESENT,root.name,root.name,"filesystem-name-observer","1",LIMITATIONS)]
 for name in TARGETS:
  path=root/name;artifact_id=context.source_artifact_ids[name]
  try:
   if not path.exists():artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.ABSENT,None,False,None));continue
   mode=path.lstat().st_mode
   if not stat.S_ISREG(mode):artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.PRESENT_INVALID_TYPE,None,False,None));continue
   if name=="Manifest.db":
    header=read_header(path);recognizable=header==b"SQLite format 3\x00";artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.PRESENT_ACCESSIBLE,recognizable,True,None));continue
   try:value=read_plist(path)
   except (plistlib.InvalidFileException,ValueError,TypeError):
    artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.PRESENT_ACCESSIBLE,False,False,"plist_malformed"));observations.append(_ob(context,artifact_id,name,None,ValueState.MALFORMED,None,None));continue
   if not isinstance(value,dict):raise ValueError("plist_root_unsupported")
   artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.PRESENT_ACCESSIBLE,True,False,None))
   for field in FIELDS[name]:
    if field not in value:observations.append(_ob(context,artifact_id,name,field,ValueState.MISSING,None,None))
    else:
     raw=value[field];supported=isinstance(raw,(str,bool,int,float,bytes,datetime))
     observations.append(_ob(context,artifact_id,name,field,ValueState.PRESENT if supported else ValueState.UNSUPPORTED,raw,raw if supported else None))
  except PermissionError:artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.PRESENT_INACCESSIBLE,None,False,"metadata_inaccessible"))
  except OSError:artifacts.append(ArtifactDiscovery(name,artifact_id,DiscoveryState.DISCOVERY_FAILED,None,False,"metadata_read_failed"))
 groups={"device_identifier":[i for i,o in enumerate(observations) if o.field_name in {"Target Identifier","Unique Identifier"}],"product_version":[i for i,o in enumerate(observations) if o.field_name=="Product Version"],"encryption":[i for i,o in enumerate(observations) if o.field_name=="IsEncrypted"],"snapshot_state":[i for i,o in enumerate(observations) if o.field_name=="SnapshotState"]}
 reconciliations=tuple(reconcile(field,observations,indexes,at=at) for field,indexes in groups.items())
 states={a.source_file:a.state for a in artifacts};manifest=next(a for a in artifacts if a.source_file=="Manifest.db")
 conflicts=any(r.outcome is ReconciliationOutcome.CONFLICT_UNRESOLVED for r in reconciliations)
 encrypted=any(o.field_name=="IsEncrypted" and o.raw_value is True for o in observations)
 if manifest.state is DiscoveryState.ABSENT:outcome=EligibilityOutcome.MANIFEST_DB_ABSENT
 elif manifest.state is not DiscoveryState.PRESENT_ACCESSIBLE or manifest.structurally_recognizable is False:outcome=EligibilityOutcome.MANIFEST_DB_VALIDATION_FAILED
 elif any(states[name] is DiscoveryState.ABSENT for name in FIELDS):outcome=EligibilityOutcome.REQUIRED_METADATA_ABSENT
 elif encrypted:outcome=EligibilityOutcome.ENCRYPTED_BACKUP_OUT_OF_SCOPE
 elif conflicts:outcome=EligibilityOutcome.DISCOVERY_COMPLETE_WITH_CONFLICTS
 elif any(a.failure_code for a in artifacts):outcome=EligibilityOutcome.DISCOVERY_COMPLETE_WITH_LIMITATIONS
 else:outcome=EligibilityOutcome.MANIFEST_DB_VALIDATION_PENDING
 return DiscoveryResult(DISCOVERY_PROFILE_ID,DISCOVERY_PROFILE_VERSION,context,tuple(artifacts),tuple(observations),reconciliations,outcome,at)
def _ob(c,artifact,name,field,state,raw,normalized):
 return MetadataObservation(c.tenant_id,c.case_id,c.evidence_source_id,artifact,c.processing_run_id,name,f"top-level:{name}","metadata_field" if field else "metadata_document",field,state,raw,normalized,"python.plistlib","1",LIMITATIONS)
