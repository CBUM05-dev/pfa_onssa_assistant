# Data Governance

All data must remain inside ONSSA infrastructure:

- Source PDFs.
- Corpus JSON.
- Chunks.
- Embeddings.
- Qdrant payloads and snapshots.
- Model artifacts.
- Logs and audit events.

No document content should be sent to external cloud AI APIs.

## Source Freshness

The source synchronization manifest stores source URLs, local paths, content hashes and last-seen timestamps.

This allows the project to detect:

- new source pages;
- new PDFs;
- changed PDFs;
- unchanged sources;
- failed downloads.
