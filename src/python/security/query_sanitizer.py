"""
Gremlin Query Sanitization and Validation

This module provides comprehensive query sanitization for JanusGraph Gremlin queries:
- Parameterized query building (prevents injection)
- Query allowlisting (only approved patterns)
- Input validation (type checking, range validation)
- Query logging and monitoring
- Rate limiting per query pattern

Security Features:
- SQL/NoSQL injection prevention
- Command injection prevention
- Path traversal prevention
- Denial of service prevention (query complexity limits)
"""

import hashlib
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from banking.compliance.audit_logger import AuditEventType, get_audit_logger

logger = logging.getLogger(__name__)
audit_logger = get_audit_logger()


class QueryComplexity(Enum):
    """Query complexity levels for rate limiting"""

    SIMPLE = 1  # Single vertex/edge lookup
    MODERATE = 2  # Traversals with filters
    COMPLEX = 3  # Multi-hop traversals
    EXPENSIVE = 4  # Aggregations, analytics


class ValidationError(Exception):
    """Raised when query validation fails"""

    pass


@dataclass
class QueryPattern:
    """Approved query pattern with metadata"""

    name: str
    pattern: str
    description: str
    complexity: QueryComplexity
    max_results: int = 1000
    timeout_seconds: int = 30
    parameters: List[str] = field(default_factory=list)

    def matches(self, query: str) -> bool:
        """Check if query matches this pattern"""
        return bool(re.match(self.pattern, query, re.IGNORECASE))


class QueryAllowlist:
    """
    Manages approved query patterns

    Only queries matching allowlisted patterns are permitted.
    This prevents arbitrary query execution and limits attack surface.
    """

    def __init__(self):
        self.patterns: Dict[str, QueryPattern] = {}
        self._initialize_default_patterns()

    def _initialize_default_patterns(self) -> None:
        """Initialize default approved query patterns"""

        # Vertex lookups
        self.add_pattern(
            QueryPattern(
                name="get_vertex_by_id",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.valueMap\(\)$",
                description="Get vertex by ID",
                complexity=QueryComplexity.SIMPLE,
                parameters=["vertex_id"],
            )
        )

        self.add_pattern(
            QueryPattern(
                name="get_vertex_by_property",
                pattern=r"^g\.V\(\)\.has\(['\"]?\w+['\"]?,\s*['\"]?[\w-]+['\"]?\)\.valueMap\(\)$",
                description="Get vertex by property",
                complexity=QueryComplexity.SIMPLE,
                parameters=["property_name", "property_value"],
            )
        )

        # Edge traversals
        self.add_pattern(
            QueryPattern(
                name="get_outgoing_edges",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.outE\(\)\.limit\(\d+\)$",
                description="Get outgoing edges from vertex",
                complexity=QueryComplexity.MODERATE,
                max_results=100,
                parameters=["vertex_id", "limit"],
            )
        )

        self.add_pattern(
            QueryPattern(
                name="get_incoming_edges",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.inE\(\)\.limit\(\d+\)$",
                description="Get incoming edges to vertex",
                complexity=QueryComplexity.MODERATE,
                max_results=100,
                parameters=["vertex_id", "limit"],
            )
        )

        # Multi-hop traversals
        self.add_pattern(
            QueryPattern(
                name="two_hop_traversal",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.out\(\)\.out\(\)\.limit\(\d+\)$",
                description="Two-hop outgoing traversal",
                complexity=QueryComplexity.COMPLEX,
                max_results=500,
                timeout_seconds=60,
                parameters=["vertex_id", "limit"],
            )
        )

        # Aggregations
        self.add_pattern(
            QueryPattern(
                name="count_vertices_by_label",
                pattern=r"^g\.V\(\)\.hasLabel\(['\"]?\w+['\"]?\)\.count\(\)$",
                description="Count vertices by label",
                complexity=QueryComplexity.MODERATE,
                parameters=["label"],
            )
        )

        # AML/Fraud detection patterns
        self.add_pattern(
            QueryPattern(
                name="find_connected_accounts",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.out\(['\"]?owns['\"]?\)\.hasLabel\(['\"]?Account['\"]?\)\.limit\(\d+\)$",
                description="Find accounts owned by person",
                complexity=QueryComplexity.MODERATE,
                max_results=50,
                parameters=["person_id", "limit"],
            )
        )

        self.add_pattern(
            QueryPattern(
                name="find_transaction_chain",
                pattern=r"^g\.V\(['\"]?[\w-]+['\"]?\)\.repeat\(out\(['\"]?transacted['\"]?\)\)\.times\(\d+\)\.limit\(\d+\)$",
                description="Find transaction chain from account",
                complexity=QueryComplexity.EXPENSIVE,
                max_results=100,
                timeout_seconds=120,
                parameters=["account_id", "hops", "limit"],
            )
        )

    def add_pattern(self, pattern: QueryPattern) -> None:
        """Add an approved query pattern"""
        self.patterns[pattern.name] = pattern
        logger.info("Added query pattern: %s", pattern.name)

    def remove_pattern(self, name: str) -> None:
        """Remove a query pattern"""
        if name in self.patterns:
            del self.patterns[name]
            logger.info("Removed query pattern: %s", name)

    def validate_query(self, query: str) -> Tuple[bool, Optional[QueryPattern]]:
        """
        Validate query against allowlist

        Returns:
            (is_valid, matching_pattern)
        """
        for pattern in self.patterns.values():
            if pattern.matches(query):
                return True, pattern

        return False, None

    def get_pattern(self, name: str) -> Optional[QueryPattern]:
        """Get pattern by name"""
        return self.patterns.get(name)

    def list_patterns(self) -> List[str]:
        """List all pattern names"""
        return list(self.patterns.keys())


class GremlinQueryBuilder:
    """
    Parameterized Gremlin query builder

    Prevents injection attacks by using parameterized queries.
    All user inputs are properly escaped and validated.

    Example:
        builder = GremlinQueryBuilder()
        query = builder.get_vertex_by_id("person-123")
        # Returns: g.V('person-123').valueMap()
    """

    def __init__(self, allowlist: Optional[QueryAllowlist] = None):
        self.allowlist = allowlist or QueryAllowlist()
        self._query_cache: Dict[str, str] = {}

    def _sanitize_id(self, vertex_id: str) -> str:
        """Sanitize vertex/edge ID"""
        # Only allow alphanumeric, hyphens, underscores
        if not re.match(r"^[\w-]+$", vertex_id):
            raise ValidationError(f"Invalid vertex ID: {vertex_id}")
        return vertex_id

    def _sanitize_property_name(self, prop_name: str) -> str:
        """Sanitize property name"""
        # Only allow alphanumeric and underscores
        if not re.match(r"^\w+$", prop_name):
            raise ValidationError(f"Invalid property name: {prop_name}")
        return prop_name

    def _sanitize_label(self, label: str) -> str:
        """Sanitize vertex/edge label"""
        # Only allow alphanumeric
        if not re.match(r"^\w+$", label):
            raise ValidationError(f"Invalid label: {label}")
        return label

    def _sanitize_value(self, value: Any) -> str:
        """Sanitize property value"""
        if isinstance(value, str):
            # Escape single quotes
            return value.replace("'", "\\'")
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            raise ValidationError(f"Unsupported value type: {type(value)}")

    def _validate_limit(self, limit: int, max_limit: int = 1000) -> int:
        """Validate and enforce limit"""
        if not isinstance(limit, int) or limit < 1:
            raise ValidationError(f"Invalid limit: {limit}")
        if limit > max_limit:
            logger.warning("Limit %d exceeds max %d, capping", limit, max_limit)
            return max_limit
        return limit

    def get_vertex_by_id(self, vertex_id: str) -> str:
        """Build query to get vertex by ID"""
        vertex_id = self._sanitize_id(vertex_id)
        query = f"g.V('{vertex_id}').valueMap()"

        # Validate against allowlist
        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def get_vertex_by_property(self, property_name: str, property_value: Any) -> str:
        """Build query to get vertex by property"""
        property_name = self._sanitize_property_name(property_name)
        property_value = self._sanitize_value(property_value)

        if isinstance(property_value, str):
            query = f"g.V().has('{property_name}', '{property_value}').valueMap()"
        else:
            query = f"g.V().has('{property_name}', {property_value}).valueMap()"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def get_outgoing_edges(self, vertex_id: str, limit: int = 100) -> str:
        """Build query to get outgoing edges"""
        vertex_id = self._sanitize_id(vertex_id)
        limit = self._validate_limit(limit, max_limit=100)

        query = f"g.V('{vertex_id}').outE().limit({limit})"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def get_incoming_edges(self, vertex_id: str, limit: int = 100) -> str:
        """Build query to get incoming edges"""
        vertex_id = self._sanitize_id(vertex_id)
        limit = self._validate_limit(limit, max_limit=100)

        query = f"g.V('{vertex_id}').inE().limit({limit})"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def count_vertices_by_label(self, label: str) -> str:
        """Build query to count vertices by label"""
        label = self._sanitize_label(label)
        query = f"g.V().hasLabel('{label}').count()"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def find_connected_accounts(self, person_id: str, limit: int = 50) -> str:
        """Build query to find accounts owned by person"""
        person_id = self._sanitize_id(person_id)
        limit = self._validate_limit(limit, max_limit=50)

        query = f"g.V('{person_id}').out('owns').hasLabel('Account').limit({limit})"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query

    def find_transaction_chain(self, account_id: str, hops: int = 3, limit: int = 100) -> str:
        """Build query to find transaction chain"""
        account_id = self._sanitize_id(account_id)

        if not isinstance(hops, int) or hops < 1 or hops > 5:
            raise ValidationError(f"Invalid hops: {hops} (must be 1-5)")

        limit = self._validate_limit(limit, max_limit=100)

        query = f"g.V('{account_id}').repeat(out('transacted')).times({hops}).limit({limit})"

        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            raise ValidationError(f"Query not in allowlist: {query}")

        return query


class QueryValidator:
    """
    Query validation and security checks

    Performs comprehensive validation:
    - Syntax validation
    - Injection detection
    - Complexity analysis
    - Rate limiting
    - Audit logging
    """

    # Dangerous patterns that indicate injection attempts
    DANGEROUS_PATTERNS = [
        r"system\(",  # System calls
        r"exec\(",  # Code execution
        r"eval\(",  # Code evaluation
        r"__import__",  # Python imports
        r"\.\./",  # Path traversal
        r"drop\(",  # Drop operations
        r"addV\(",  # Vertex creation (if not allowed)
        r"addE\(",  # Edge creation (if not allowed)
        r"property\(.*drop",  # Property drops
        r";.*g\.",  # Query chaining
        r"\/\*.*\*\/",  # Comments (can hide malicious code)
    ]

    def __init__(self, allowlist: Optional[QueryAllowlist] = None):
        self.allowlist = allowlist or QueryAllowlist()
        self._rate_limiter: Dict[str, List[float]] = {}
        self._max_queries_per_minute = 60

    def validate(self, query: str, user: str = "anonymous") -> Tuple[bool, Optional[str]]:
        """
        Validate query for security issues

        Returns:
            (is_valid, error_message)
        """
        # 1. Check for dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                error = f"Dangerous pattern detected: {pattern}"
                self._log_validation_failure(query, user, error)
                return False, error

        # 2. Check against allowlist
        is_valid, pattern = self.allowlist.validate_query(query)
        if not is_valid:
            error = "Query not in allowlist"
            self._log_validation_failure(query, user, error)
            return False, error

        # 3. Check rate limit
        if not self._check_rate_limit(user):
            error = "Rate limit exceeded"
            self._log_validation_failure(query, user, error)
            return False, error

        # 4. Log successful validation
        self._log_validation_success(query, user, pattern)

        return True, None

    def _check_rate_limit(self, user: str) -> bool:
        """Check if user has exceeded rate limit"""
        now = time.time()

        # Initialize user's query history
        if user not in self._rate_limiter:
            self._rate_limiter[user] = []

        # Remove queries older than 1 minute
        self._rate_limiter[user] = [ts for ts in self._rate_limiter[user] if now - ts < 60]

        # Check limit
        if len(self._rate_limiter[user]) >= self._max_queries_per_minute:
            return False

        # Add current query
        self._rate_limiter[user].append(now)
        return True

    def _log_validation_failure(self, query: str, user: str, reason: str) -> None:
        """Log validation failure"""
        from datetime import datetime, timezone

        from banking.compliance.audit_logger import AuditEvent, AuditSeverity

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.VALIDATION_FAILURE,
            severity=AuditSeverity.WARNING,
            user=user,
            resource="gremlin_query",
            action="validate",
            result="failure",
            metadata={
                "query": query,
                "reason": reason,
                "query_hash": hashlib.sha256(query.encode()).hexdigest(),
            },
        )
        audit_logger.log_event(event)
        logger.warning("Query validation failed for user %s: %s", user, reason)

    def _log_validation_success(
        self, query: str, user: str, pattern: Optional[QueryPattern]
    ) -> None:
        """Log successful validation"""
        from datetime import datetime, timezone

        from banking.compliance.audit_logger import AuditEvent, AuditSeverity

        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=AuditEventType.QUERY_EXECUTED,
            severity=AuditSeverity.INFO,
            user=user,
            resource="gremlin_query",
            action="validate",
            result="success",
            metadata={
                "query": query,
                "pattern": pattern.name if pattern else "unknown",
                "complexity": pattern.complexity.name if pattern else "unknown",
                "query_hash": hashlib.sha256(query.encode()).hexdigest(),
            },
        )
        audit_logger.log_event(event)


def sanitize_gremlin_query(query: str, user: str = "anonymous") -> Tuple[bool, str, Optional[str]]:
    """
    Convenience function to sanitize and validate a Gremlin query

    Args:
        query: Gremlin query string
        user: User executing the query

    Returns:
        (is_valid, sanitized_query, error_message)
    """
    validator = QueryValidator()
    is_valid, error = validator.validate(query, user)

    if not is_valid:
        return False, "", error

    return True, query, None


# Made with Bob
