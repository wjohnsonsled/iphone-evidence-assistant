\# PRD-003 — MVP Scope



\## 1. Product objective



Build a secure, evidence-aware application that accepts a supported Apple local

iPhone backup and helps investigators and attorneys understand approved forensic

artifacts using search, timelines, source inspection, and evidence-grounded AI.



\## 2. Supported input objective



The MVP will support structurally valid Apple local backups.



The MVP must detect whether a backup is:



\- unencrypted;

\- encrypted;

\- incomplete;

\- malformed;

\- or unsupported.



The initial implementation should prioritize unencrypted Apple local backups.



Encrypted backups may be detected and reported, but decryption is not required

for the first supported release unless separately approved.



\## 3. Initial supported artifact candidates



The following are candidates for complete MVP support, subject to repository

inspection, schema research, implementation, validation, and testing:



1\. Backup metadata

&#x20;  - Info.plist

&#x20;  - Status.plist

&#x20;  - Manifest.plist

&#x20;  - Manifest.db



2\. Backup file inventory

&#x20;  - file identifier

&#x20;  - domain

&#x20;  - relative path

&#x20;  - file size

&#x20;  - source location

&#x20;  - SHA-256

&#x20;  - availability status



3\. Messages

&#x20;  - SMS

&#x20;  - iMessage

&#x20;  - chats

&#x20;  - handles

&#x20;  - supported message fields

&#x20;  - direction where determinable



4\. Message attachments

&#x20;  - attachment metadata

&#x20;  - message relationship

&#x20;  - source path

&#x20;  - hash

&#x20;  - MIME type where determinable



5\. Call history



6\. Contacts



Additional artifact families require separate approval.



\## 4. Required product capabilities



\### 4.1 Case management



\- Create a case.

\- Record case name and internal identifier.

\- Associate evidence sources with a case.

\- Prevent cross-case and cross-tenant access.

\- Record material case actions.



\### 4.2 Backup ingestion



\- Accept a selected or uploaded Apple local backup.

\- Validate required files and structure.

\- Detect encryption state.

\- Generate an intake inventory.

\- Hash source files.

\- Preserve source evidence unchanged.

\- Record errors and omissions.

\- Produce a coverage report.



\### 4.3 Artifact processing



\- Process only approved artifact families.

\- Preserve raw source values.

\- Generate normalized records.

\- Maintain source provenance.

\- Record parser name and version.

\- Record processing status per artifact family.

\- Fail visibly when complete processing cannot be established.



\### 4.4 Search and review



\- Search supported artifact records.

\- Filter by artifact type, participant, date, and source.

\- Open the source-backed record.

\- Display original and normalized values.

\- Display provenance and processing limitations.



\### 4.5 Timeline



\- Normalize supported timestamps to UTC.

\- Preserve original timestamp values.

\- Present a chronological view.

\- Allow filtering and source inspection.

\- Do not represent uncertain event ordering as exact.



\### 4.6 Evidence-grounded AI



\- Answer questions only from authorized supported records.

\- Cite supporting records.

\- Allow citation inspection.

\- Distinguish facts from interpretation.

\- State uncertainty and limitations.

\- Refuse unsupported conclusions.

\- Never treat the AI response as source evidence.



\### 4.7 Reporting



\- Produce an attorney-readable report.

\- Include scope, sources, methods, findings, citations, and limitations.

\- Avoid legal conclusions.

\- Include processing coverage and unsupported artifact disclosures.



\## 5. Out of scope for the first release



\- Physical acquisition

\- Full filesystem acquisition

\- Jailbreaking

\- Device exploitation

\- Cellebrite extraction ingestion

\- GrayKey extraction ingestion

\- Deleted-data recovery

\- Unallocated-space recovery

\- Complete iPhone representation

\- Complete application coverage

\- Health database analysis

\- Keychain or saved-password extraction

\- Credential recovery

\- Malware detection

\- Spyware detection

\- Attribution of actions to a physical person

\- Intent or motive determination

\- Legal conclusions

\- Automatic testimony opinions



\## 6. MVP success criteria



The MVP is successful when it can:



1\. Accept a validated supported unencrypted Apple local backup.

2\. Produce a complete source-file inventory.

3\. Process each approved artifact family without silent omissions.

4\. Link every normalized record to its source artifact.

5\. Search and review supported records.

6\. answer evidence-grounded questions with inspectable citations;

7\. Generate a professional report containing sources and limitations.

8\. Pass approved validation fixtures and regression tests.

9\. Explicitly report unsupported, inaccessible, corrupted, or failed data.

