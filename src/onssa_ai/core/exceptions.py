"""Domain exceptions for the ONSSA AI service."""


class OnssaAIError(Exception):
    """Base exception for service-level failures."""


class ConfigurationError(OnssaAIError):
    """Raised when configuration is invalid or incomplete."""


class CorpusValidationError(OnssaAIError):
    """Raised when the knowledge corpus does not meet required invariants."""


class InsufficientEvidenceError(OnssaAIError):
    """Raised when RAG cannot find enough evidence to answer reliably."""
