# Code Refactoring Guide

## Document Information

- **Document Version:** 1.0.0
- **Last Updated:** 2026-01-28
- **Owner:** Engineering Team
- **Review Cycle:** Quarterly

---

## Executive Summary

This guide provides comprehensive guidelines for refactoring the HCD JanusGraph codebase to improve maintainability, readability, and performance. It identifies technical debt, provides refactoring strategies, and establishes code quality standards.

### Refactoring Goals

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Code Duplication | 15% | <5% | 67% reduction |
| Cyclomatic Complexity | Avg 12 | <10 | 17% reduction |
| Function Length | Avg 45 lines | <30 lines | 33% reduction |
| Test Coverage | 70% | 85% | 21% increase |
| Technical Debt Ratio | 8% | <3% | 63% reduction |

---

## Table of Contents

1. [Technical Debt Inventory](#technical-debt-inventory)
2. [Refactoring Priorities](#refactoring-priorities)
3. [Code Quality Standards](#code-quality-standards)
4. [Refactoring Patterns](#refactoring-patterns)
5. [Automated Tools](#automated-tools)
6. [Testing Strategy](#testing-strategy)
7. [Migration Plan](#migration-plan)

---

## 1. Technical Debt Inventory

### 1.1 Code Duplication

**Identified Duplications:**

```python
# BEFORE: Duplicated connection logic
# File: src/python/client/janusgraph_client.py
def connect_to_graph():
    connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
    g = traversal().withRemote(connection)
    return g

# File: src/python/init/initialize_graph.py
def connect_to_graph():
    connection = DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
    g = traversal().withRemote(connection)
    return g

# AFTER: Centralized connection utility
# File: src/python/utils/graph_connection.py
class GraphConnectionManager:
    """Centralized graph connection management."""
    
    @staticmethod
    def create_connection(host='localhost', port=8182):
        """Create graph connection with proper configuration."""
        connection = DriverRemoteConnection(
            f'ws://{host}:{port}/gremlin',
            'g',
            pool_size=20,
            max_inflight=64
        )
        return traversal().withRemote(connection)
```

**Refactoring Actions:**
1. Extract common connection logic to utility module
2. Create reusable configuration management
3. Implement connection pooling
4. Add proper error handling

### 1.2 Long Functions

**Example: Complex Query Function**

```python
# BEFORE: 80-line function with multiple responsibilities
def process_user_data(user_id):
    # Validation (10 lines)
    if not user_id:
        raise ValueError("User ID required")
    if not isinstance(user_id, str):
        raise TypeError("User ID must be string")
    # ... more validation
    
    # Database query (20 lines)
    connection = create_connection()
    try:
        user = g.V(user_id).next()
        friends = g.V(user_id).out('knows').toList()
        # ... more queries
    finally:
        connection.close()
    
    # Data processing (30 lines)
    processed_data = {}
    for friend in friends:
        # Complex processing logic
        pass
    
    # Response formatting (20 lines)
    response = format_response(processed_data)
    return response

# AFTER: Refactored into smaller, focused functions
class UserDataProcessor:
    """Process user data with clear separation of concerns."""
    
    def __init__(self, graph_connection):
        self.g = graph_connection
    
    def process(self, user_id: str) -> Dict[str, Any]:
        """Main processing pipeline."""
        self._validate_user_id(user_id)
        user_data = self._fetch_user_data(user_id)
        processed = self._process_data(user_data)
        return self._format_response(processed)
    
    def _validate_user_id(self, user_id: str):
        """Validate user ID."""
        if not user_id:
            raise ValueError("User ID required")
        if not isinstance(user_id, str):
            raise TypeError("User ID must be string")
    
    def _fetch_user_data(self, user_id: str) -> Dict[str, Any]:
        """Fetch user data from graph."""
        user = self.g.V(user_id).next()
        friends = self.g.V(user_id).out('knows').toList()
        return {'user': user, 'friends': friends}
    
    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process fetched data."""
        # Processing logic
        return processed_data
    
    def _format_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format response."""
        # Formatting logic
        return formatted_response
```

### 1.3 Magic Numbers and Strings

```python
# BEFORE: Magic values scattered throughout code
def check_query_performance(execution_time):
    if execution_time > 1000:  # What is 1000?
        log_slow_query()
    
    if result_count > 10000:  # Why 10000?
        paginate_results()

# AFTER: Named constants with documentation
class QueryPerformanceConfig:
    """Query performance configuration constants."""
    
    # Slow query threshold in milliseconds
    SLOW_QUERY_THRESHOLD_MS = 1000
    
    # Maximum results before pagination required
    MAX_RESULTS_BEFORE_PAGINATION = 10000
    
    # Connection pool size
    DEFAULT_POOL_SIZE = 20
    
    # Query timeout in seconds
    DEFAULT_QUERY_TIMEOUT = 30

def check_query_performance(execution_time):
    """Check query performance against thresholds."""
    if execution_time > QueryPerformanceConfig.SLOW_QUERY_THRESHOLD_MS:
        log_slow_query()
    
    if result_count > QueryPerformanceConfig.MAX_RESULTS_BEFORE_PAGINATION:
        paginate_results()
```

### 1.4 Poor Error Handling

```python
# BEFORE: Generic exception handling
def execute_query(query):
    try:
        result = g.V().has('name', query).toList()
        return result
    except Exception as e:
        print(f"Error: {e}")
        return []

# AFTER: Specific exception handling with proper logging
class QueryExecutionError(Exception):
    """Custom exception for query execution errors."""
    pass

def execute_query(query: str) -> List[Any]:
    """
    Execute graph query with proper error handling.
    
    Args:
        query: Query string
    
    Returns:
        Query results
    
    Raises:
        QueryExecutionError: If query execution fails
    """
    try:
        result = g.V().has('name', query).toList()
        logger.info(f"Query executed successfully: {query}")
        return result
    
    except GremlinServerError as e:
        logger.error(f"Gremlin server error: {e}", exc_info=True)
        raise QueryExecutionError(f"Query failed: {e}") from e
    
    except ConnectionError as e:
        logger.error(f"Connection error: {e}", exc_info=True)
        raise QueryExecutionError("Database connection failed") from e
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise QueryExecutionError(f"Unexpected error: {e}") from e
```

---

## 2. Refactoring Priorities

### Priority 1: Critical (Week 10)
1. **Extract duplicate code** - Reduce duplication from 15% to <10%
2. **Break down long functions** - Max 30 lines per function
3. **Improve error handling** - Specific exceptions, proper logging
4. **Add type hints** - 100% coverage for public APIs

### Priority 2: High (Week 11)
1. **Refactor complex classes** - Single Responsibility Principle
2. **Improve naming** - Clear, descriptive names
3. **Add docstrings** - All public functions/classes
4. **Remove dead code** - Unused imports, functions, variables

### Priority 3: Medium (Week 12)
1. **Optimize imports** - Remove unused, organize properly
2. **Improve code organization** - Logical module structure
3. **Add configuration management** - Centralized config
4. **Enhance logging** - Structured logging throughout

---

## 3. Code Quality Standards

### 3.1 Python Style Guide

**Follow PEP 8 with project-specific rules:**

```python
# Line length: 100 characters (not 79)
# Use double quotes for strings
# Use trailing commas in multi-line structures

# GOOD
def process_data(
    user_id: str,
    include_friends: bool = True,
    max_depth: int = 2,
) -> Dict[str, Any]:
    """
    Process user data with configurable options.
    
    Args:
        user_id: User identifier
        include_friends: Whether to include friend data
        max_depth: Maximum traversal depth
    
    Returns:
        Processed user data dictionary
    
    Raises:
        ValueError: If user_id is invalid
    """
    pass
```

### 3.2 Type Hints

**Required for all public APIs:**

```python
from typing import List, Dict, Optional, Union, Any
from dataclasses import dataclass

@dataclass
class User:
    """User data model."""
    user_id: str
    name: str
    email: str
    age: Optional[int] = None
    friends: List[str] = field(default_factory=list)

def get_user(user_id: str) -> Optional[User]:
    """Get user by ID."""
    pass

def get_users(
    filters: Dict[str, Any],
    limit: int = 100
) -> List[User]:
    """Get users with filters."""
    pass
```

### 3.3 Documentation Standards

**Docstring format (Google style):**

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    One-line summary of function purpose.
    
    Longer description explaining the function's behavior,
    edge cases, and any important implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        param3: Optional description of param3. Defaults to None.
    
    Returns:
        Dictionary containing:
            - key1: Description of key1
            - key2: Description of key2
    
    Raises:
        ValueError: If param1 is empty
        TypeError: If param2 is negative
    
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'value1'
    
    Note:
        This function has O(n) time complexity.
    """
    pass
```

---

## 4. Refactoring Patterns

### 4.1 Extract Method

**When to use:** Function > 30 lines or doing multiple things

```python
# BEFORE
def process_order(order_data):
    # Validate (10 lines)
    # Calculate total (15 lines)
    # Apply discounts (20 lines)
    # Save to database (10 lines)
    # Send notification (10 lines)
    pass

# AFTER
def process_order(order_data):
    validated_data = validate_order(order_data)
    total = calculate_total(validated_data)
    final_total = apply_discounts(total, validated_data)
    order_id = save_order(validated_data, final_total)
    send_notification(order_id)
    return order_id
```

### 4.2 Replace Magic Number with Constant

```python
# BEFORE
if age > 18:
    grant_access()

# AFTER
MINIMUM_AGE = 18

if age > MINIMUM_AGE:
    grant_access()
```

### 4.3 Introduce Parameter Object

```python
# BEFORE
def create_user(name, email, age, city, country, phone):
    pass

# AFTER
@dataclass
class UserData:
    name: str
    email: str
    age: int
    city: str
    country: str
    phone: str

def create_user(user_data: UserData):
    pass
```

### 4.4 Replace Conditional with Polymorphism

```python
# BEFORE
def calculate_price(product_type, base_price):
    if product_type == 'book':
        return base_price * 0.9
    elif product_type == 'electronics':
        return base_price * 1.1
    elif product_type == 'food':
        return base_price * 1.05

# AFTER
class Product(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float) -> float:
        pass

class Book(Product):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 0.9

class Electronics(Product):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 1.1

class Food(Product):
    def calculate_price(self, base_price: float) -> float:
        return base_price * 1.05
```

---

## 5. Automated Tools

### 5.1 Code Formatting

**Black - Automatic code formatting:**

```bash
# Install
pip install black

# Format all Python files
black src/ tests/

# Check without modifying
black --check src/

# Configuration in pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### 5.2 Import Sorting

**isort - Organize imports:**

```bash
# Install
pip install isort

# Sort imports
isort src/ tests/

# Configuration in pyproject.toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### 5.3 Linting

**pylint - Code analysis:**

```bash
# Install
pip install pylint

# Run linter
pylint src/

# Configuration in .pylintrc
[MASTER]
max-line-length=100
disable=C0111,  # missing-docstring
        C0103,  # invalid-name
        R0903   # too-few-public-methods
```

**flake8 - Style guide enforcement:**

```bash
# Install
pip install flake8

# Run flake8
flake8 src/

# Configuration in .flake8
[flake8]
max-line-length = 100
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

### 5.4 Type Checking

**mypy - Static type checking:**

```bash
# Install
pip install mypy

# Run type checker
mypy src/

# Configuration in mypy.ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### 5.5 Code Complexity

**radon - Complexity metrics:**

```bash
# Install
pip install radon

# Check cyclomatic complexity
radon cc src/ -a -nb

# Check maintainability index
radon mi src/ -nb

# Thresholds
# CC: A (1-5), B (6-10), C (11-20), D (21-50), E (51-100), F (100+)
# MI: A (20-100), B (10-19), C (0-9)
```

### 5.6 Security Scanning

**bandit - Security issues:**

```bash
# Install
pip install bandit

# Scan for security issues
bandit -r src/

# Configuration in .bandit
[bandit]
exclude_dirs = ['/test']
tests = ['B201', 'B301']
skips = ['B101', 'B601']
```

---

## 6. Testing Strategy

### 6.1 Test Coverage Goals

```bash
# Install coverage
pip install coverage pytest-cov

# Run tests with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Coverage targets
# Overall: 85%
# Critical modules: 95%
# Utility modules: 80%
```

### 6.2 Test Organization

```
tests/
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_client.py
│   ├── test_security.py
│   └── test_performance.py
├── integration/          # Integration tests (slower)
│   ├── test_graph_operations.py
│   └── test_api_endpoints.py
├── performance/          # Performance tests
│   └── test_benchmarks.py
└── conftest.py          # Shared fixtures
```

---

## 7. Migration Plan

### Week 10: Critical Refactoring

**Day 1-2: Setup and Analysis**
- Configure automated tools
- Run initial code analysis
- Identify high-priority issues

**Day 3-4: Core Refactoring**
- Extract duplicate code
- Break down long functions
- Add type hints to public APIs

**Day 5: Testing and Validation**
- Run full test suite
- Verify no regressions
- Update documentation

### Week 11: Quality Improvements

**Day 1-2: Code Organization**
- Refactor complex classes
- Improve module structure
- Organize imports

**Day 3-4: Documentation**
- Add comprehensive docstrings
- Update API documentation
- Create code examples

**Day 5: Final Review**
- Code review
- Performance testing
- Documentation review

---

## Appendices

### Appendix A: Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.8

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Appendix B: CI/CD Integration

```yaml
# .github/workflows/code-quality.yml
name: Code Quality
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.8'
      
      - name: Install dependencies
        run: |
          pip install black isort flake8 mypy pylint radon bandit
      
      - name: Run Black
        run: black --check src/
      
      - name: Run isort
        run: isort --check-only src/
      
      - name: Run flake8
        run: flake8 src/
      
      - name: Run mypy
        run: mypy src/
      
      - name: Run pylint
        run: pylint src/
      
      - name: Check complexity
        run: radon cc src/ -a -nb --total-average
      
      - name: Security scan
        run: bandit -r src/
```

---

**Document Classification:** Internal - Technical  
**Next Review Date:** 2026-04-28  
**Document Owner:** Engineering Team