\# FOR-004 — Artifact Support Matrix



\## Support rule



No artifact family is supported merely because its source file is present.



Support requires:



\- approved source path or discovery method;

\- approved schema profile;

\- complete declared field coverage;

\- relationship and timestamp handling;

\- provenance;

\- error detection;

\- validation fixtures;

\- regression tests;

\- documented limitations;

\- and successful processing.



\## Initial matrix



| Artifact ID | Artifact family | Expected source | Input type | Target status | MVP |

|---|---|---|---|---|---|

| BAK-001 | Backup metadata | Info.plist | Both | Candidate | Yes |

| BAK-002 | Backup status | Status.plist | Both | Candidate | Yes |

| BAK-003 | Backup manifest metadata | Manifest.plist | Both | Candidate | Yes |

| BAK-004 | Backup file manifest | Manifest.db | Both | Candidate | Yes |

| BAK-005 | Backup file inventory | Derived from Manifest.db | Both | Candidate | Yes |

| MSG-001 | SMS/iMessage messages | HomeDomain/Library/SMS/sms.db | Both | Candidate | Yes |

| MSG-002 | Chats | sms.db | Both | Candidate | Yes |

| MSG-003 | Handles | sms.db | Both | Candidate | Yes |

| MSG-004 | Message attachments | sms.db and attachment files | Both | Candidate | Yes |

| CALL-001 | Call history | Supported CallHistory source | Both | Candidate | Yes |

| CON-001 | Contacts | Supported AddressBook sources | Both | Candidate | Yes |

| NOTE-001 | Notes | Supported Notes sources | Both | Unsupported | No |

| SAF-001 | Safari history | Supported Safari sources | Both | Unsupported | No |

| CAL-001 | Calendar | Supported Calendar sources | Both | Unsupported | No |

| HLT-001 | Health | Encrypted backup only | Encrypted | Unsupported | No |

| KEY-001 | Keychain-derived records | Encrypted backup only | Encrypted | Unsupported | No |

| DEL-001 | Deleted records | Multiple | Both | Unsupported | No |

| APP-001 | Arbitrary third-party apps | Multiple | Both | Unsupported | No |



\## Controlled support statuses



\- CANDIDATE

\- IN\_DEVELOPMENT

\- VALIDATION\_PENDING

\- SUPPORTED\_COMPLETE

\- SUPPORTED\_NO\_RECORDS

\- UNSUPPORTED

\- DEPRECATED



\## Required per-artifact details



Before an artifact may become `SUPPORTED\_COMPLETE`, add:



\- supported iOS versions;

\- supported schema fingerprints;

\- source paths;

\- required companion files;

\- parsed tables;

\- parsed fields;

\- excluded fields;

\- join behavior;

\- timestamp behavior;

\- directionality rules;

\- source-record locator format;

\- known limitations;

\- validation dataset;

\- expected results;

\- parser version;

\- test names;

\- review approval.

