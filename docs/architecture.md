# Architecture

The service is an on-premise AI backend consumed by the existing ONSSA platform.

## Boundaries

- The API provides regulatory AI capabilities only.
- The existing ONSSA platform remains the user-facing system.
- No external cloud AI or remote embedding service is allowed.

## First Vertical Slice

```text
Regulation -> Transversal Regulation -> Food Safety
```

## Runtime Components

- FastAPI API service.
- vLLM production inference service for Qwen3 8B Instruct.
- Qdrant vector database.
- Prometheus and Grafana monitoring.
- Nginx reverse proxy.

## Knowledge Rule

Regulatory facts must come from retrieved corpus evidence. Fine-tuning controls behavior and formatting, not factual memory.
