# Operations

Operational checks:

- API health: `/health`
- API readiness: `/ready`
- Qdrant collection status.
- vLLM model availability.
- Prometheus targets.
- Grafana dashboards.

Backups should include Qdrant snapshots, configs, corpus files, and model adapters.

## Source Synchronization

Run manually:

```bash
python scripts/sync_onssa_sources.py --config configs/sources.yaml
```

Or with Make:

```bash
make sync-sources
```

The script writes:

- pages to `data/raw/pages/onssa/`;
- PDFs to `data/raw/pdfs/onssa/`;
- change manifest to `data/sources/onssa_manifest.json`.

For production, schedule this command with cron or systemd timer on the ONSSA server.
