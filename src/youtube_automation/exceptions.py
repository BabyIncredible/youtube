"""Project-specific exceptions with user-facing failure categories."""


class ConfigurationError(ValueError):
    """Raised when project configuration is missing or invalid."""


class ProviderResponseError(RuntimeError):
    """Raised when a provider returns malformed or unusable data."""


class PipelineStateError(RuntimeError):
    """Raised when persisted pipeline state cannot be safely handled."""
