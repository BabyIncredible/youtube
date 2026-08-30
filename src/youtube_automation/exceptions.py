"""Project-specific exceptions with user-facing failure categories."""


class ConfigurationError(ValueError):
    """Raised when project configuration is missing or invalid."""


class ProviderAuthenticationError(RuntimeError):
    """Raised when provider credentials are missing or rejected."""


class ProviderRateLimitError(RuntimeError):
    """Raised when a provider temporarily rejects requests due to its quota."""


class ProviderResponseError(RuntimeError):
    """Raised when a provider returns malformed or unusable data."""


class PipelineStateError(RuntimeError):
    """Raised when persisted pipeline state cannot be safely handled."""
