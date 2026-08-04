# Owner Checklist — Controlled Apple Test Fixture

- [ ] Use a lawfully owned/controlled dedicated test iPhone.
- [ ] Assign a non-sensitive package ID; use only owner-controlled test accounts.
- [ ] Remove unrelated accounts/data before acquisition; never use client,
  litigation, employee, family, confidential business, credential, health,
  financial, location, or uncontrolled cloud data.
- [ ] Record device model, exact iOS/build, host OS, Apple Devices version,
  timezone, operator, ownership basis, and account-control basis.
- [ ] Prepare unique benign tokens for SMS/iMessage, one-to-one and practical
  group threads, synthetic contacts, incoming/outgoing/missed calls, and small
  non-sensitive attachments.
- [ ] Execute each event and record actual time, direction, participants,
  disposition, attachment identity, and independent screenshot/observation reference.
- [ ] Create one **unencrypted** local backup with Apple Devices for Windows;
  record start/end and do not modify the completed backup.
- [ ] Store it outside Git in approved encrypted-at-rest, access-controlled storage.
- [ ] Never email it, publish a link, upload it to CI/source control/an LLM, or
  share it outside the controlled validation environment.
- [ ] Complete manifest, ground-truth, custody, minimization, retention, and
  destruction records; record SHA-256 before/after controlled transfer.
- [ ] Provide Codex only the package ID and separately approved controlled
  access instructions—never commit or paste backup contents.
- [ ] **STOP and request separate validation authorization before processing.**
