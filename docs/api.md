# API

## Health

```text
GET /health
GET /ready
```

## RAG Answer

```text
POST /api/v1/rag/answer
```

The endpoint must return a refusal when retrieved evidence is insufficient.

## Search

```text
POST /api/v1/search
```

Returns retrieved regulatory evidence chunks with metadata and scores.
