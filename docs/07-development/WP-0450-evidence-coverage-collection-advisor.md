# WP-0450 — Evidence Coverage & Collection Advisor

## Status

- Governance: approved for backlog insertion by DEC-0027
- Implementation: BLOCKED by foundational dependencies
- Support effect: none

WP-0450 is the reconciled identifier for the requested “WP-0400 Evidence
Coverage & Collection Advisor.” Existing WP-0400 and DEV-0401 through DEV-0410
remain the controlling Supported Evidence Data Model.

## Closed candidate coverage meanings

| State | Meaning |
|---|---|
| PRESENT | The specifically identified source/artifact observation is present; completeness is not implied |
| SOURCE_PRESENT_NOT_PROCESSED | Source exists but approved processing did not complete |
| NOT_COLLECTED | The evidence-source family was not received |
| BACKUP_METHOD_EXCLUDED | The acquisition method is documented not to include the item/family |
| CLOUD_DEPENDENT_POSSIBLE | The item may exist in a separate cloud source; not directly established |
| UNSUPPORTED | Required parser/artifact behavior is not owner-promoted Supported |
| NOT_APPLICABLE | A versioned rule establishes the category does not apply to the defined measurable set |
| UNKNOWN | Available observations cannot support another state |
| VALIDATION_FAILED | Required validation failed operationally |
| RESOURCE_LIMIT_EXCEEDED | Processing was denied by an explicit resource ceiling |
| PARTIALLY_AVAILABLE | A precisely identified subset is available and omissions/failures are explicit |

DEV-0453 must version, validate, and freeze exact semantics before use.

## Mandatory conclusion basis

Every conclusion must retain observation basis, evidence source, stable
file/manifest reference when applicable, validation result, support-registry
state, parser authorization/execution state, normalized and rejected record
results, rule ID/version, limitations, and provenance references.

## Permanent forensic rules

- Backup absence is not device absence, deletion, concealment, wiping,
  corruption, destruction, or spoliation.
- Application presence does not prove all application data was included.
- Unsupported parsing is `UNSUPPORTED`, never “no evidence found.”
- Zero records remains distinct from not executed, not authorized, absent
  source, unsupported source, validation/resource failure, and partial failure.
- Cloud-dependent material stays possible or indeterminate unless validated
  metadata directly establishes otherwise.
- A percentage names its exact measurable numerator and denominator and never
  represents all evidence that existed on a device.
- Recommendations reproduce from stored observations and versioned rules.
