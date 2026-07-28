from datetime import datetime, timezone
from uuid import UUID
import pytest
from app.evidence_core.typed_value import *
def u(n:int)->UUID:return UUID(f"46000000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def rep(state, value=None, failure=None):
    return representation(state=state,type_id="synthetic",serialization_profile_id="text-v1",serialization_profile_version="1",serialized_value=value,failure_code=failure)
@pytest.mark.parametrize("state,value",[ (ValueState.NULL,None),(ValueState.MISSING,None),(ValueState.EMPTY,""),(ValueState.FALSE,"false"),(ValueState.ZERO,"0"),(ValueState.UNKNOWN,None)])
def test_semantic_states_remain_distinct(state,value):
    item=rep(state,value); assert item.state is state and item.serialized_value==value
@pytest.mark.parametrize("state,code",[(ValueState.UNSUPPORTED,"unsupported_type"),(ValueState.UNREPRESENTABLE,"serialization_failed")])
def test_failed_states_are_explicit(state,code):
    assert rep(state,None,code).failure_code==code
def test_raw_and_normalized_are_separate_with_provenance():
    raw=rep(ValueState.VALUE,"001"); norm=rep(ValueState.VALUE,"1")
    tx=ValueTransformation(u(1),"decimal-normalization","1",u(2),u(3),NOW,("Synthetic only.",))
    item=observe_typed_value(source_artifact_id=u(4),processing_run_id=u(2),parser_identity_id=u(3),observed_at=NOW,raw=raw,normalized=norm,transformation=tx)
    assert item.raw.serialized_value=="001" and item.normalized.serialized_value=="1"
    assert item.raw.representation_id != item.normalized.representation_id
@pytest.mark.parametrize("state,value,failure",[(ValueState.NULL,"null",None),(ValueState.VALUE,None,None),(ValueState.UNSUPPORTED,None,None),(ValueState.ZERO,"0","bad")])
def test_invalid_coercions_fail(state,value,failure):
    with pytest.raises(ValueError): rep(state,value,failure)
def test_normalized_requires_transformation():
    with pytest.raises(ValueError): observe_typed_value(source_artifact_id=u(4),processing_run_id=u(2),parser_identity_id=None,observed_at=NOW,raw=rep(ValueState.VALUE,"x"),normalized=rep(ValueState.VALUE,"X"))
