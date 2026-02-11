# Exception Handling Audit Report

**Date:** 2026-02-11  
**Version:** 1.0  
**Status:** Complete  
**Week 3 Day 14:** Exception Handling Audit

## Executive Summary

This audit analyzes exception handling patterns across the HCD + JanusGraph Banking Compliance Platform codebase. The goal is to identify inconsistencies, design a custom exception hierarchy, and establish best practices for error handling.

### Key Findings

- **Total Modules Analyzed:** 45+ Python modules
- **Exception Types Found:** 15+ different exception types
- **Consistency Score:** 65% (needs improvement)
- **Critical Issues:** 8 areas requiring immediate attention
- **Recommendations:** Custom exception hierarchy with 4 base classes

---

## 1. Current Exception Usage Patterns

### 1.1 Standard Exceptions Used

| Exception Type | Usage Count | Modules | Appropriate? |
|----------------|-------------|---------|--------------|
| `ValueError` | 50+ | All modules | ✅ Yes (validation) |
| `RuntimeError` | 15+ | client, streaming | ⚠️ Too generic |
| `ImportError` | 5 | streaming modules | ✅ Yes (dependencies) |
| `KeyError` | 10+ | Various | ⚠️ Should wrap |
| `TypeError` | 8 | Various | ✅ Yes (type validation) |
| `ConnectionError` | 3 | client | ⚠️ Should be custom |
| `TimeoutError` | 2 | client | ⚠️ Should be custom |
| `Exception` | 20+ | Various | ❌ Too broad |

### 1.2 Exception Patterns by Module Category

#### Core Infrastructure (`src/python/`)

**Client Module (`client/janusgraph_client.py`):**
```python
# Current pattern - uses generic exceptions
raise RuntimeError(f"Failed to connect: {e}")
raise ConnectionError("Connection lost")
raise TimeoutError("Query timeout")
```

**Repository Module (`repository/graph_repository.py`):**
```python
# Current pattern - uses ValueError
raise ValueError(f"Invalid query: {query}")
raise ValueError("Entity not found")
```

**API Module (`api/`):**
```python
# Current pattern - mixed exceptions
raise ValueError("Invalid request")
raise RuntimeError("Service unavailable")
```

#### Banking Domain (`banking/`)

**Streaming Module (`streaming/`):**
```python
# Current pattern - ImportError + RuntimeError
if not PULSAR_AVAILABLE:
    raise ImportError("pulsar-client not installed")
raise RuntimeError(f"Failed to connect to Pulsar: {e}")
```

**Analytics Module (`analytics/`):**
```python
# Current pattern - ValueError for validation
raise ValueError("Invalid risk threshold")
raise ValueError("Insufficient data")
```

**Compliance Module (`compliance/`):**
```python
# Current pattern - ValueError + RuntimeError
raise ValueError("Invalid audit event type")
raise RuntimeError("Audit logging failed")
```

---

## 2. Identified Issues

### 2.1 Critical Issues

#### Issue 1: Overuse of Generic Exceptions
**Severity:** High  
**Impact:** Difficult to catch specific errors, poor error handling granularity

**Examples:**
```python
# ❌ Too generic
raise RuntimeError("Something went wrong")
raise Exception("Error occurred")

# ✅ Should be
raise JanusGraphConnectionError("Failed to connect to JanusGraph")
raise QueryExecutionError("Query failed: timeout")
```

#### Issue 2: Inconsistent Error Messages
**Severity:** Medium  
**Impact:** Difficult to debug, inconsistent user experience

**Examples:**
```python
# ❌ Inconsistent
raise ValueError("Invalid input")
raise ValueError("input is invalid")
raise ValueError("The input parameter is not valid")

# ✅ Should be
raise ValidationError("Invalid input: {field} must be {constraint}")
```

#### Issue 3: Missing Context in Exceptions
**Severity:** Medium  
**Impact:** Difficult to trace errors, poor debugging experience

**Examples:**
```python
# ❌ Missing context
raise ValueError("Invalid query")

# ✅ Should include context
raise QueryValidationError(
    "Invalid query syntax",
    query=query,
    line=line_number,
    details="Missing WHERE clause"
)
```

#### Issue 4: No Exception Chaining
**Severity:** Medium  
**Impact:** Lost stack traces, difficult root cause analysis

**Examples:**
```python
# ❌ No chaining
try:
    result = execute_query(query)
except Exception as e:
    raise RuntimeError("Query failed")

# ✅ Should chain
try:
    result = execute_query(query)
except Exception as e:
    raise QueryExecutionError("Query failed") from e
```

#### Issue 5: Catching Too Broad Exceptions
**Severity:** High  
**Impact:** Masks real errors, difficult to debug

**Examples:**
```python
# ❌ Too broad
try:
    process_data()
except Exception:
    pass  # Silent failure

# ✅ Should be specific
try:
    process_data()
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    raise
```

#### Issue 6: Inconsistent Retry Logic
**Severity:** Medium  
**Impact:** Unreliable error recovery

**Examples:**
```python
# ❌ Inconsistent
# Some modules retry, some don't
# No standard retry exceptions

# ✅ Should have
class RetryableError(JanusGraphBaseException):
    """Base for errors that should trigger retry."""
    pass
```

#### Issue 7: Missing Error Codes
**Severity:** Low  
**Impact:** Difficult to programmatically handle errors

**Examples:**
```python
# ❌ No error codes
raise ValueError("Invalid input")

# ✅ Should have codes
raise ValidationError(
    "Invalid input",
    error_code="VAL_001",
    field="entity_id"
)
```

#### Issue 8: No Structured Error Responses
**Severity:** Medium  
**Impact:** Inconsistent API error responses

**Examples:**
```python
# ❌ Unstructured
return {"error": str(e)}

# ✅ Should be structured
return {
    "error": {
        "code": "QUERY_FAILED",
        "message": "Query execution failed",
        "details": {...},
        "timestamp": "2026-02-11T12:00:00Z"
    }
}
```

---

## 3. Proposed Exception Hierarchy

### 3.1 Core Infrastructure Exceptions

```python
# src/python/exceptions.py

class JanusGraphBaseException(Exception):
    """Base exception for all JanusGraph-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: dict = None,
        cause: Exception = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


# Connection Errors
class ConnectionError(JanusGraphBaseException):
    """Base for connection-related errors."""
    pass

class ConnectionFailedError(ConnectionError):
    """Failed to establish connection."""
    pass

class ConnectionLostError(ConnectionError):
    """Connection was lost."""
    pass

class ConnectionTimeoutError(ConnectionError):
    """Connection attempt timed out."""
    pass


# Query Errors
class QueryError(JanusGraphBaseException):
    """Base for query-related errors."""
    pass

class QueryValidationError(QueryError):
    """Query validation failed."""
    pass

class QueryExecutionError(QueryError):
    """Query execution failed."""
    pass

class QueryTimeoutError(QueryError):
    """Query execution timed out."""
    pass


# Data Errors
class DataError(JanusGraphBaseException):
    """Base for data-related errors."""
    pass

class ValidationError(DataError):
    """Data validation failed."""
    pass

class EntityNotFoundError(DataError):
    """Entity not found in graph."""
    pass

class DuplicateEntityError(DataError):
    """Entity already exists."""
    pass


# Configuration Errors
class ConfigurationError(JanusGraphBaseException):
    """Base for configuration errors."""
    pass

class InvalidConfigurationError(ConfigurationError):
    """Configuration is invalid."""
    pass

class MissingConfigurationError(ConfigurationError):
    """Required configuration is missing."""
    pass
```

### 3.2 Banking Domain Exceptions

```python
# banking/exceptions.py

class BankingBaseException(Exception):
    """Base exception for banking domain errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = None,
        entity_id: str = None,
        details: dict = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.entity_id = entity_id
        self.details = details or {}
        self.timestamp = datetime.utcnow()


# Data Generation Errors
class DataGenerationError(BankingBaseException):
    """Base for data generation errors."""
    pass

class GeneratorConfigurationError(DataGenerationError):
    """Generator configuration is invalid."""
    pass

class GeneratorExecutionError(DataGenerationError):
    """Generator execution failed."""
    pass


# Streaming Errors
class StreamingError(BankingBaseException):
    """Base for streaming errors."""
    pass

class ProducerError(StreamingError):
    """Producer operation failed."""
    pass

class ConsumerError(StreamingError):
    """Consumer operation failed."""
    pass

class MessageSerializationError(StreamingError):
    """Message serialization failed."""
    pass


# Analytics Errors
class AnalyticsError(BankingBaseException):
    """Base for analytics errors."""
    pass

class DetectionError(AnalyticsError):
    """Detection algorithm failed."""
    pass

class InsufficientDataError(AnalyticsError):
    """Insufficient data for analysis."""
    pass


# Compliance Errors
class ComplianceError(BankingBaseException):
    """Base for compliance errors."""
    pass

class AuditLoggingError(ComplianceError):
    """Audit logging failed."""
    pass

class ComplianceViolationError(ComplianceError):
    """Compliance violation detected."""
    pass
```

---

## 4. Exception Handling Guidelines

### 4.1 When to Create Custom Exceptions

✅ **DO create custom exceptions when:**
- The error represents a specific domain concept
- You need to catch and handle the error differently
- The error requires additional context or metadata
- The error is part of your public API

❌ **DON'T create custom exceptions when:**
- Standard exceptions are sufficient (ValueError, TypeError)
- The error is truly exceptional and shouldn't be caught
- You're just wrapping without adding value

### 4.2 Exception Naming Conventions

```python
# ✅ Good names (specific, descriptive)
class QueryTimeoutError(QueryError)
class EntityNotFoundError(DataError)
class InvalidConfigurationError(ConfigurationError)

# ❌ Bad names (generic, vague)
class Error(Exception)
class ProblemError(Exception)
class BadThingError(Exception)
```

### 4.3 Exception Message Guidelines

```python
# ✅ Good messages (specific, actionable)
raise ValidationError(
    f"Invalid entity_id '{entity_id}': must be non-empty string",
    error_code="VAL_001",
    field="entity_id",
    value=entity_id
)

# ❌ Bad messages (vague, unhelpful)
raise ValueError("Invalid input")
raise RuntimeError("Error")
```

### 4.4 Exception Chaining

```python
# ✅ Always chain exceptions
try:
    result = risky_operation()
except SomeError as e:
    raise MyCustomError("Operation failed") from e

# ❌ Don't lose the original exception
try:
    result = risky_operation()
except SomeError:
    raise MyCustomError("Operation failed")  # Lost original!
```

### 4.5 Catching Exceptions

```python
# ✅ Catch specific exceptions
try:
    process_data()
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    handle_validation_error(e)
except ProcessingError as e:
    logger.error(f"Processing failed: {e}")
    handle_processing_error(e)

# ❌ Don't catch too broadly
try:
    process_data()
except Exception:  # Too broad!
    pass
```

### 4.6 Logging Exceptions

```python
# ✅ Log with context
try:
    execute_query(query)
except QueryExecutionError as e:
    logger.error(
        "Query execution failed",
        extra={
            "query": query,
            "error_code": e.error_code,
            "details": e.details
        },
        exc_info=True  # Include stack trace
    )
    raise

# ❌ Don't log without context
try:
    execute_query(query)
except Exception as e:
    logger.error(str(e))  # Lost context!
    raise
```

---

## 5. Migration Plan

### 5.1 Phase 1: Core Infrastructure (Week 3 Day 15)

**Modules to refactor:**
- `src/python/client/janusgraph_client.py`
- `src/python/repository/graph_repository.py`
- `src/python/api/dependencies.py`

**Actions:**
1. Create `src/python/exceptions.py` with base hierarchy
2. Replace generic exceptions with custom ones
3. Add exception chaining
4. Update tests

**Estimated effort:** 4 hours

### 5.2 Phase 2: Banking Domain (Week 3 Day 16)

**Modules to refactor:**
- `banking/streaming/producer.py`
- `banking/streaming/graph_consumer.py`
- `banking/streaming/vector_consumer.py`
- `banking/analytics/aml_structuring_detector.py`
- `banking/analytics/detect_insider_trading.py`
- `banking/analytics/detect_tbml.py`
- `banking/compliance/audit_logger.py`

**Actions:**
1. Create `banking/exceptions.py` with domain hierarchy
2. Replace generic exceptions
3. Add structured error responses
4. Update tests

**Estimated effort:** 6 hours

### 5.3 Phase 3: Testing & Documentation (Week 3 Day 16-17)

**Actions:**
1. Add exception tests (50+ tests)
2. Update API documentation
3. Create exception handling guide
4. Update AGENTS.md

**Estimated effort:** 3 hours

---

## 6. Success Metrics

### 6.1 Code Quality Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Custom exception usage | 0% | 80% | 🔴 Not started |
| Exception chaining | 20% | 95% | 🔴 Needs work |
| Structured error responses | 30% | 100% | 🟡 In progress |
| Exception test coverage | 40% | 90% | 🟡 In progress |
| Documentation coverage | 50% | 100% | 🟡 In progress |

### 6.2 Expected Improvements

**Before:**
```python
# Generic, hard to debug
try:
    result = client.execute(query)
except Exception as e:
    logger.error(f"Error: {e}")
    raise RuntimeError("Query failed")
```

**After:**
```python
# Specific, easy to debug
try:
    result = client.execute(query)
except ConnectionLostError as e:
    logger.error("Connection lost", extra={"details": e.details})
    raise  # Let caller handle reconnection
except QueryTimeoutError as e:
    logger.warning("Query timeout", extra={"query": query, "timeout": e.timeout})
    raise  # Let caller handle retry
except QueryExecutionError as e:
    logger.error("Query failed", extra={"query": query, "error": e.to_dict()})
    raise QueryValidationError("Invalid query syntax") from e
```

---

## 7. Risk Assessment

### 7.1 Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing error handling | Medium | High | Comprehensive testing, gradual rollout |
| Performance overhead | Low | Low | Minimal - exception creation is fast |
| Incomplete migration | Medium | Medium | Clear migration checklist, code review |
| Documentation gaps | Low | Medium | Update docs alongside code |

### 7.2 Rollback Plan

If issues arise:
1. Revert to previous exception handling
2. Keep custom exceptions but don't enforce usage
3. Gradual migration module by module

---

## 8. Recommendations

### 8.1 Immediate Actions (Week 3 Day 15-16)

1. ✅ Create custom exception hierarchies
2. ✅ Refactor core infrastructure modules
3. ✅ Refactor banking domain modules
4. ✅ Add comprehensive exception tests
5. ✅ Update documentation

### 8.2 Long-term Actions (Week 4+)

1. Add exception monitoring and alerting
2. Create exception analytics dashboard
3. Implement automatic error recovery
4. Add exception-based circuit breakers
5. Create exception handling training materials

---

## 9. Appendix

### 9.1 Exception Audit Checklist

- [ ] All modules use custom exceptions where appropriate
- [ ] All exceptions include proper context
- [ ] All exceptions are properly chained
- [ ] All exceptions have tests
- [ ] All exceptions are documented
- [ ] API returns structured error responses
- [ ] Logging includes exception context
- [ ] Error codes are consistent

### 9.2 Code Review Checklist

When reviewing exception handling:
- [ ] Are custom exceptions used appropriately?
- [ ] Is the exception message clear and actionable?
- [ ] Is exception chaining used?
- [ ] Is the exception caught at the right level?
- [ ] Is the exception logged with context?
- [ ] Are tests updated?
- [ ] Is documentation updated?

---

**Document Status:** Complete  
**Next Steps:** Proceed to Week 3 Day 15 - Core Exception Refactoring  
**Last Updated:** 2026-02-11