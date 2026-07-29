# FOR-015 — Manifest.db Domain Grammar Profile

## Profile

- Profile: `manifestdb-domain-grammar` version 1
- Source: `Files.domain` from `manifestdb-files-query` version 1 or 2
- Decisions: DEC-0065 implementation; DEC-0066 candidate completion
- Status: COMPLETE candidate infrastructure, not Supported

The profile preserves the exact raw SQLite value, storage class, upstream value
state, tenant/case/source/artifact/controlled-copy/database/run identities,
ROWID locator, query and locator profiles, observation time, and limitations.
It performs no filesystem access and creates no supported evidence record.

## Candidate grammar

Exact, case-sensitive literals are `HomeDomain`, `WirelessDomain`,
`RootDomain`, `SystemPreferencesDomain`, `ManagedPreferencesDomain`,
`MediaDomain`, and `CameraRollDomain`.

Exact candidate prefixes are `AppDomain-`, `AppDomainGroup-`,
`AppDomainPlugin-`, `SysContainerDomain-`, and
`SysSharedContainerDomain-`. Their suffix is retained as an opaque application,
group, or plugin component only when it begins with ASCII alphanumeric and
contains only ASCII alphanumeric, period, or hyphen characters.

These forms are repository-characterized, provisional candidate grammar
validated only with synthetic fixtures. They are not asserted as an exhaustive
or authoritative Apple specification. Exact recognized TEXT is its own
canonical representation; no transformation occurs.

Unknown ASCII forms remain `UNKNOWN_STRUCTURE`. Empty, non-ASCII, whitespace,
bad-prefix-component, NULL, unsupported SQLite storage classes, unavailable,
read-failed, unevaluated, and indeterminate observations remain separately
represented. No value is trimmed, case-folded, Unicode-normalized, repaired,
or coerced.

## Permanent limitations

Recognition does not establish application installation, execution, ownership,
or user activity. A component is not a verified bundle identifier. A domain
does not establish a container, file, physical object, artifact, backup
completeness, Apple compatibility, or support. Unknown grammar may exist.
Synthetic fixtures are not Apple-produced. No parser, artifact, input,
workflow, API, or capability is Supported.
