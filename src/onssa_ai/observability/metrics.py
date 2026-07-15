"""Prometheus metric placeholders."""

from prometheus_client import Counter

RAG_REQUESTS_TOTAL = Counter("onssa_rag_requests_total", "Total RAG answer requests.")
RAG_REFUSALS_TOTAL = Counter("onssa_rag_refusals_total", "Total refused RAG answers.")
