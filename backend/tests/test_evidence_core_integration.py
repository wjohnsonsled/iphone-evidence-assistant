from app.evidence_core.quarantine_store import QuarantinedOutputStore
from app.evidence_core.supported_store import SupportedEvidenceStore
from app.support.registry import create_supported_registry


def test_default_composition_has_empty_supported_store_and_separate_quarantine():
    supported = SupportedEvidenceStore(create_supported_registry())
    quarantined = QuarantinedOutputStore()
    assert supported.count == 0
    assert type(supported) is not type(quarantined)
    assert not {"transfer", "promote"} & set(dir(quarantined))
