"""Audit logging placeholder."""

import structlog

logger = structlog.get_logger(__name__)


def audit_event(event: str, **fields: object) -> None:
    logger.info(event, **fields)
