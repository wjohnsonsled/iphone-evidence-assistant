# DEV-0102 — Dependency Locking and Reproducible Environment Acceptance

- Status: VALIDATION_PENDING
- Dependencies: DEV-0101 complete
- Scope: Python dependency resolution and backend container install
- Runtime behavior effect: none
- Support effect: none

## Requirements

| ID | Requirement |
|---|---|
| DEV-0102-R01 | Record exact versions for all resolved runtime, development, and build Python dependencies |
| DEV-0102-R02 | Ensure every direct `pyproject.toml` dependency is represented by an exact lock pin |
| DEV-0102-R03 | Reject ranges, malformed pins, and duplicate normalized package names deterministically |
| DEV-0102-R04 | Pin the backend Python image to the validated Python 3.12 patch line |
| DEV-0102-R05 | Install locked dependencies before installing the application non-editably, without build isolation or re-resolution |
| DEV-0102-R06 | Document a clean local environment workflow and offline lock verification command |
| DEV-0102-R07 | Preserve the supported/legacy composition boundary and runtime behavior |
| DEV-0102-R08 | Use no evidence, secrets, external service, API exposure, migration, or support promotion |

## Acceptance criteria

- AC-01: lock contains only unique exact pins.
- AC-02: lock covers every direct runtime/dev declaration.
- AC-03: malformed/range/duplicate/missing-direct tests fail deterministically.
- AC-04: a clean repository-local environment installs the lock and package
  with `--no-deps --no-build-isolation`, subject to locally available package
  caches/network.
- AC-05: `pip check`, imports, focused tests, and full regressions pass.
- AC-06: Dockerfile uses the lock, noneditable application install, and pinned
  Python patch image.
- AC-07: documentation states regeneration, verification, limitations, and
  that Compose uses synthetic/empty development inputs only.
- AC-08: no application behavior, migration, API surface, or support status
  changes.

## Validation record

| Criterion | Result | Evidence |
|---|---|---|
| AC-01 | PASS | Offline validator accepted 38 unique exact pins |
| AC-02 | PASS | Runtime, development, and build declarations are covered |
| AC-03 | PASS | Range, duplicate, and missing-direct negative tests passed |
| AC-04 | PASS | Repository-local clean environment installed the lock and noneditable package with build isolation disabled |
| AC-05 | PASS | `pip check`; import smoke; backend 85/85; legacy 5/5; compileall |
| AC-06 | PASS | Static Docker assertions verify patch image and locked noneditable installation |
| AC-07 | PASS | README and local-development instructions updated |
| AC-08 | PASS | Diff contains no application, API, migration, evidence, or support-status behavior |

## Commands and limitations

- `python backend/scripts/verify_lock.py --project backend/pyproject.toml --lock backend/requirements.lock`
- clean repository-local `venv`, locked install, `--no-deps --no-build-isolation`
  package install, `pip check`, and import smoke test
- `python -m pytest backend --basetemp tmp/pytest-dev0102-full-20260727`
- `python -m unittest discover -s tests`
- `python -m compileall -q backend/app backend/scripts`
- `git diff --check`

Docker is not installed in the available environment, so the image itself was
not built. Deterministic tests inspect its install contract. The accepted
repository-local pytest base-temporary-directory workaround was required
because the operating-system pytest directory is inaccessible. The accepted
third-party TestClient deprecation warning remains. Exact locking establishes
repeatable dependency selection, not vulnerability freedom or byte-identical
container reproduction.
