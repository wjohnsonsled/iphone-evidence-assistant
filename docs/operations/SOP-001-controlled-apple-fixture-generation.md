# SOP-001 — Generate a Controlled Apple Test Fixture

Current package: `CAF-2026-001`. Processing is not authorized.

1. Confirm device ownership/authorization; assign package ID; create controlled
   test accounts; open the ground-truth and custody worksheets; record device,
   host, Apple Devices, OS/build, and timezone details.
2. Before acquisition, minimize the device: remove unrelated accounts and
   content, exclude secrets and unnecessary photo/email/health/financial/
   location/cloud data, create synthetic contacts and small benign attachments.
3. Execute the event plan. Use unique benign tokens and separated timestamps.
   Record actual execution, operator, direction, participants, call disposition,
   attachment identity, and independent confirmation. Do not edit completed records.
4. In Apple Devices for Windows, create one unencrypted local backup. Record
   software version and start/end times. Do not alter the backup after creation.
5. Identify—not open—the backup root. Register package/source identity and use
   the existing controlled SHA-256/custody process for initial, pre-transfer,
   post-transfer, and controlled-copy observations. Keep source read-only.
6. Transfer only through an approved secured channel; verify hashes on receipt;
   store encrypted at rest with named access controls, outside Git and public services.
7. Complete minimization, retention/destruction, custody, ground-truth, package,
   and validation-matrix records. Do not place host absolute paths or secrets in them.
8. Stop. Request separate owner authorization naming the exact package ID before
   any backup file is opened, copied for analysis, or processed.
