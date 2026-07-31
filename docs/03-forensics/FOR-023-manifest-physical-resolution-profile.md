# FOR-023 — Candidate Manifest Physical-Resolution Profile

Profile `manifest-fileid-physical-object-resolution` version 1 compares a
DEV-0603 canonical Manifest `fileID` with DEV-0621 candidate physical-object
filename observations in the same tenant, case, evidence source, and processing
run. The exact provisional rule is lowercase 40-character ASCII hexadecimal
equality beneath the directory named by the first two characters.

Outcomes distinguish exact single and multiple matches, no match under complete
or partial inventory, non-comparable identifiers, inaccessible or unsupported
objects, scope mismatch, profile incompatibility, and validation failure.

This profile is based only on project-original synthetic fixtures. A match is a
filename observation, not content verification. No match is not deletion,
device absence, tampering, or backup incompleteness. The profile provides no
Apple compatibility, artifact, parser, workflow, or support status.
