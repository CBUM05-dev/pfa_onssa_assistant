# Deployment

Target operating system: Ubuntu Server 24.04 LTS.

## Production Services

- `api`
- `vllm`
- `qdrant`
- `nginx`
- `prometheus`
- `grafana`

## Production Start

```bash
docker compose -f deployment/compose/docker-compose.prod.yml up -d
docker compose -f deployment/compose/docker-compose.monitoring.yml up -d
```

Production deployments must mount local model artifacts and corpus data from ONSSA infrastructure.
