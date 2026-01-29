"""
Custom exceptions for JanusGraph client operations.

File: exceptions.py
Created: 2026-01-28
Author: David LECONTE - IBM Worldwide | Data & AI
"""


class JanusGraphError(Exception):
    """Base exception for all JanusGraph client errors."""

    pass


class ConnectionError(JanusGraphError):
    """Raised when connection to JanusGraph server fails."""

    pass


class QueryError(JanusGraphError):
    """Raised when a Gremlin query execution fails."""

    def __init__(self, message: str, query: str | None = None) -> None:
        """
        Initialize query error.

        Args:
            message: Error description
            query: The Gremlin query that failed (optional)
        """
        super().__init__(message)
        self.query = query


class TimeoutError(JanusGraphError):
    """Raised when an operation times out."""

    pass


class ValidationError(JanusGraphError):
    """Raised when input validation fails."""

    pass
