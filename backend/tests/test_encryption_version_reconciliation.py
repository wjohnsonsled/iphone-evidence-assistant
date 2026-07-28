from datetime import datetime,timezone
from app.discovery.apple_backup import *
from app.discovery.metadata_readers import encryption_version_reconciliation
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def result(outcome=ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION):
 product=ReconciliationResult(RECONCILIATION_PROFILE_ID,"1","product_version",(1,),outcome,"17" if outcome is not ReconciliationOutcome.CONFLICT_UNRESOLVED else None,"single_source_only" if outcome is ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION else None,ConflictCategory.PRODUCT_VERSION_CONFLICT if outcome is ReconciliationOutcome.CONFLICT_UNRESOLVED else None,NOW,LIMITATIONS)
 encryption=ReconciliationResult(RECONCILIATION_PROFILE_ID,"1","encryption",(2,),ReconciliationOutcome.SINGLE_SOURCE_OBSERVATION,False,"single_source_only",None,NOW,LIMITATIONS)
 return DiscoveryResult(DISCOVERY_PROFILE_ID,"1",None,(),(),(product,encryption),EligibilityOutcome.MANIFEST_DB_VALIDATION_PENDING,NOW) # type: ignore[arg-type]
def test_exact_reconciliation_preserves_source_result_without_compatibility_meaning():
 claims=encryption_version_reconciliation(result())
 assert claims.profile_id=="encryption-version-exact-reconciliation" and claims.profile_version=="1"
 assert [item.selected_value for item in claims.results]==["17",False]
 assert not {"compatible","supported","preferred_source"} & set(claims.__dataclass_fields__)
def test_product_conflict_remains_unresolved():
 claims=encryption_version_reconciliation(result(ReconciliationOutcome.CONFLICT_UNRESOLVED))
 product=claims.results[0]
 assert product.selected_value is None and product.conflict_category is ConflictCategory.PRODUCT_VERSION_CONFLICT
