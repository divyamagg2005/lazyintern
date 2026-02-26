from __future__ import annotations


class LazyInternError(Exception):
    pass


class ConfigError(LazyInternError):
    pass


class ExternalServiceError(LazyInternError):
    pass


class DeduplicationError(LazyInternError):
    pass

