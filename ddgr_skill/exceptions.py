"""Custom exceptions for ddgr_skill."""


class DdgRSkillError(Exception):
    """Base exception for ddgr-skill."""
    pass


class DdgrNotFoundError(DdgRSkillError):
    """ddgr binary not found in PATH."""
    pass


class DdgrSearchError(DdgRSkillError):
    """ddgr subprocess failed or returned invalid JSON."""
    pass


class FetchError(DdgRSkillError):
    """Failed to fetch URL content."""
    pass


class NetworkError(FetchError):
    """Network-level failure (timeout, connection refused, SSL)."""
    pass


class HTTPError(FetchError):
    """Non-200 HTTP response."""
    pass


class ContentQualityError(FetchError):
    """Fetched content failed quality validation."""
    pass


class NoResultsError(DdgRSkillError):
    """No usable results could be obtained."""
    pass

