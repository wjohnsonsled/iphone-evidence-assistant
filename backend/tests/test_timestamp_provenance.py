from datetime import datetime, timezone
from uuid import UUID
import pytest
from app.evidence_core.timestamp_provenance import *
from app.evidence_core.typed_value import ValueState, representation
def u(n): return UUID(f"47000000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
RAW=representation(state=ValueState.VALUE,type_id="timestamp-text",serialization_profile_id="utf8",serialization_profile_version="1",serialized_value="2026-11-01 01:30:00")
def base(**change):
 d=dict(source_artifact_id=u(1),source_locator_id=u(2),processing_run_id=u(3),parser_identity_id=None,observed_at=NOW,raw=RAW,category=TimestampCategory.LOCAL_DATE_TIME,precision=TimestampPrecision.SECOND,precision_reference=None,timezone=TimezoneContext(TimezoneSource.UNKNOWN),interpretation_status=InterpretationStatus.NOT_ATTEMPTED,local_time_status=LocalTimeStatus.LOCAL_TIME_STATUS_UNKNOWN,numeric_epoch=None,limitations=("Unconverted observation.",)); return d|change
def test_vocabularies_are_complete():
 assert len(TimestampCategory)==9 and len(TimestampPrecision)==11 and len(TimezoneSource)==13
 assert len(InterpretationStatus)==7 and len(LocalTimeStatus)==5 and len(ConversionStatus)==13
def test_unconverted_observation_remains_valid():
 assert observe_timestamp(**base()).raw is RAW
def test_ambiguity_and_nonexistent_are_distinct():
 assert observe_timestamp(**base(local_time_status=LocalTimeStatus.AMBIGUOUS_LOCAL_TIME)).local_time_status is LocalTimeStatus.AMBIGUOUS_LOCAL_TIME
 assert observe_timestamp(**base(local_time_status=LocalTimeStatus.NONEXISTENT_LOCAL_TIME)).local_time_status is LocalTimeStatus.NONEXISTENT_LOCAL_TIME
def test_inferred_timezone_requires_complete_basis():
 with pytest.raises(ValueError): TimezoneContext(TimezoneSource.INFERRED_WITH_DOCUMENTED_BASIS)
def test_offset_does_not_imply_named_zone():
 c=TimezoneContext(TimezoneSource.EXPLICIT_OFFSET_IN_VALUE,utc_offset="-04:00")
 assert c.zone_identifier is None
def test_numeric_epoch_requires_explicit_metadata():
 with pytest.raises(ValueError): observe_timestamp(**base(category=TimestampCategory.NUMERIC_EPOCH_VALUE))
def test_source_defined_precision_requires_reference():
 with pytest.raises(ValueError): observe_timestamp(**base(precision=TimestampPrecision.SOURCE_DEFINED))
def test_conversion_failure_is_explicit_and_keeps_source_reference():
 c=TimestampConversion(u(4),u(5),u(3),None,"safe-convert","1",NOW,None,None,TimezoneContext(TimezoneSource.UNKNOWN),ConversionStatus.CONVERSION_FAILED,"ambiguous",("No instant selected.",))
 assert c.result is None and c.source_observation_id==u(5)
def test_converted_requires_separate_derived_value():
 with pytest.raises(ValueError): TimestampConversion(u(4),u(5),u(3),None,"safe","1",NOW,None,None,TimezoneContext(TimezoneSource.NOT_APPLICABLE),ConversionStatus.CONVERTED,None,("Synthetic.",))
