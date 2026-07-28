# DEV-0411 — Legacy and Experimental Store Isolation

| ID | Acceptance criterion |
|---|---|
| AC-01 | Candidate, experimental, and legacy diagnostic output uses a separate store and record type. |
| AC-02 | Approved output is rejected from the quarantine store. |
| AC-03 | Quarantine store exposes no transfer, promotion, admission, or broad enumeration API. |
| AC-04 | Supported store remains empty and rejects non-approved dispositions independently. |
| AC-05 | Tenant/case queries constrain before return and cross-scope queries disclose nothing. |
| AC-06 | No legacy parser import, execution, migration, API, real evidence, or support promotion occurs. |

## Validation record

All AC-01 through AC-06 pass. Focused: 35 passed. Backend: 307 passed with
the accepted warning. Compilation and diff checks pass. No parser execution,
migration, API, evidence, or support behavior was added.
