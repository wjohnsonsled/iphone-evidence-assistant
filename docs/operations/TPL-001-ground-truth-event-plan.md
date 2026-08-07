# Ground-Truth Event Plan Template

Current working package: `CAF-2026-001`. Keep this template reusable.

For each event record: event ID; artifact family/type; planned local time;
planned UTC when determinable; timezone basis; synthetic participants;
direction; benign unique content token; attachment identity; call disposition;
contact relationship; device action; operator; execution status/time;
independent screenshot/observation reference; expected source/logical record;
backup expectation; observation disposition; and limitations.

States are independent: `PLANNED`, `EXECUTED`, `INDEPENDENTLY_OBSERVED`,
`BACKED_UP`, `EXPECTED_IN_BACKUP`, `OBSERVED_BY_CANDIDATE`, `NOT_OBSERVED`,
`EXTRA_OBSERVATION`, `UNSUPPORTED`, `INDETERMINATE`. Execution never implies
that a record must exist in the backup.
