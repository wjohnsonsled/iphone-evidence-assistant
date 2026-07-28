from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime,timezone
from uuid import UUID
import pytest
from app.processing.idempotency import *
def u(n):return UUID(f"11070000-0000-4000-8000-{n:012d}")
NOW=datetime(2026,7,28,tzinfo=timezone.utc)
def inputs(**changes):
 base=RequestInputs(u(1),u(2),u(3),u(4),"synthetic.parser","1","contract-v1","synthetic","schema-v1","process-v1","1","parse","a"*64,"AUTH-1")
 return replace(base,**changes)
def test_key_is_deterministic_versioned_and_exact_scope():
 first=generate_key(inputs(),generated_at=NOW);second=generate_key(inputs(),generated_at=NOW)
 assert first.idempotency_key==second.idempotency_key and len(first.idempotency_key)==64
 for change in ({"tenant_id":u(9)},{"case_id":u(9)},{"source_artifact_id":u(9)},{"parser_version":"2"},{"processing_profile_version":"2"},{"controlled_input_digest":"b"*64},{"idempotency_profile_version":"2"}):
  assert generate_key(inputs(**change),generated_at=NOW).idempotency_key!=first.idempotency_key
def test_duplicate_before_running_does_not_create_run():
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo)
 first=service.submit(inputs(),now=NOW);duplicate=service.submit(inputs(),now=NOW)
 assert first.code=="IDEMPOTENCY_CLAIM_CREATED" and duplicate.code=="DUPLICATE_REQUEST_PENDING"
 assert duplicate.request.request_id==first.request.request_id and repo.attempts(first.request.request_id)==()
def test_running_completed_and_failed_duplicate_behaviors():
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo);claim=service.submit(inputs(),now=NOW)
 run=service.start(claim.request,now=NOW)
 assert service.submit(inputs(),now=NOW).code=="DUPLICATE_REQUEST_RUNNING"
 completed=service.finish(claim.request,run,status=RequestStatus.COMPLETED)
 assert service.submit(inputs(),now=NOW).code=="DUPLICATE_REQUEST_COMPLETED"
 changed=service.submit(inputs(parser_version="2"),now=NOW)
 assert changed.request.request_id!=claim.request.request_id
 repo2=InMemoryAtomicRequestRepository();svc2=IdempotencyService(repo2);c2=svc2.submit(inputs(),now=NOW);r2=svc2.start(c2.request,now=NOW);svc2.finish(c2.request,r2,status=RequestStatus.FAILED)
 assert svc2.submit(inputs(),now=NOW).code=="EXPLICIT_RETRY_REQUIRED"
def test_retry_rerun_new_identity_monotonic_and_linked():
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo);claim=service.submit(inputs(),now=NOW)
 first=service.start(claim.request,now=NOW);failed=service.finish(claim.request,first,status=RequestStatus.FAILED)
 retry=service.retry(claim.request,failed,now=NOW,reason="explicit_retry")
 completed_retry=service.finish(claim.request,retry,status=RequestStatus.COMPLETED)
 rerun=service.rerun(claim.request,completed_retry,now=NOW,reason="examiner_rerun")
 assert len({first.run_id,retry.run_id,rerun.run_id})==3
 assert [a.attempt_number for a in repo.attempts(claim.request.request_id)]==[1,2,3]
 assert [r.relationship_type for r in repo.relationships]==[RelationshipType.RETRY_OF,RelationshipType.RERUN_OF]
 assert failed.status is RequestStatus.FAILED
def test_partial_cancel_retry_and_expired_claim_recovery():
 for status in (RequestStatus.PARTIAL,RequestStatus.CANCELLED):
  repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo);claim=service.submit(inputs(),now=NOW);prior=service.finish(claim.request,service.start(claim.request,now=NOW),status=status)
  assert service.retry(claim.request,prior,now=NOW,reason="explicit").run_id!=prior.run_id
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo);claim=service.submit(inputs(),now=NOW);service.expire(claim.request)
 recovered=service.submit(inputs(),now=NOW)
 assert recovered.code=="IDEMPOTENCY_CLAIM_CREATED" and recovered.request.request_id!=claim.request.request_id
def test_prior_relationship_required_and_cycles_rejected_without_hidden_mutation():
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo);claim=service.submit(inputs(),now=NOW);run=service.start(claim.request,now=NOW)
 before=repo.attempts(claim.request.request_id)
 with pytest.raises(ValueError,match="relationship_required"):service.start(claim.request,now=NOW,prior=run)
 assert repo.attempts(claim.request.request_id)==before
 with pytest.raises(ValueError,match="cycle"):repo.add_relationship(RunRelationship(u(8),run.run_id,run.run_id,RelationshipType.RETRY_OF,"x","Synthetic.","AUTH",NOW,("Synthetic.",)))
def test_concurrent_identical_claim_has_single_winner():
 repo=InMemoryAtomicRequestRepository();service=IdempotencyService(repo)
 with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:service.submit(inputs(),now=NOW),range(20)))
 assert sum(r.code=="IDEMPOTENCY_CLAIM_CREATED" for r in results)==1
 assert len({r.request.request_id for r in results})==1
