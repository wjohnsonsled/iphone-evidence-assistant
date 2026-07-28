# Synthetic Apple Metadata Corpus

`corpus.json` is generated-by-description synthetic test data. It contains no
values copied from a client, device, Apple-produced backup, or forensic image.
Identifiers are repeated placeholder hexadecimal characters.

The corpus tests candidate metadata discovery, plist claim projection,
normalization, encryption observation, and factual coverage only. Its passing
does not validate Apple backup compatibility, any Manifest.db schema, a parser,
an artifact family, or support status.

`Manifest.db` content is limited to the public SQLite file-header marker because
DEV-0601 remains the schema compatibility gate.
