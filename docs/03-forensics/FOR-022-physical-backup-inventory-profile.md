# FOR-022 — Physical Apple Backup Object Inventory Profile

## Profiles

- `apple-local-backup-physical-inventory` version 1
- `apple-backup-physical-object-locator` version 1
- Decision: DEC-0081
- Status: candidate synthetic characterization; not Supported

## Authorized universe

The reader requires a validated and explicitly authorized Apple local-backup
root plus exact tenant, case, evidence-source, controlled-source, and processing
run context. The authorized scope tuple must match. Missing, unauthorized,
unvalidated, non-directory, inaccessible, or link roots fail closed.

## Provisional v1 layout

The reader observes the root and only one child level below exact lowercase
two-ASCII-hex directories. A candidate physical object is a regular file whose
exact lowercase 40-ASCII-hex name begins with that directory component. This
rule is project-defined and synthetically characterized, not Apple-authoritative
or a compatibility statement.

Recognized top-level metadata is observed but excluded from candidate physical
objects. Unknown files/directories, noncanonical names, extensions, prefix
mismatches, unsupported types, and inaccessible entries remain explicit
observations. Unexpected directories are not recursively traversed.

## Type and locator controls

Types distinguish regular file, directory, symbolic link, Windows reparse
point, other special object, inaccessible, and indeterminate. Links/reparse and
special types are never followed or eligible.

Locators preserve exact case/components relative to the authorized root and
bind source/run and both profile versions. They contain no absolute or
temporary path, drive letter, host URI, enumeration position, or memory
reference.

## Resources and limitations

Caller-supplied positive ceilings govern entries, regular files, directories,
depth, pathname length, individual/aggregate hash bytes, deterministic memory
estimate, elapsed time, concurrent hashes, unresolved objects, and
cancellation. V1 depth is exactly two. Termination preserves completed
observations and the last safe locator.

Physical observation is not device existence, authenticity, content/artifact
type, deletion, concealment, tampering, significance, Apple compatibility,
parser support, or backup completeness.

