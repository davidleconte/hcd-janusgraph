"""
Graph Repository
================

Single source-of-truth for every Gremlin traversal used by the application.
Routers and services call typed methods instead of building traversals inline.

Design decisions
----------------
* Accepts a pre-built ``GraphTraversalSource`` (``g``) so the caller owns
  connection lifecycle (matches the existing ``get_graph_connection()`` pattern).
* Every public method returns plain Python dicts / primitives — no Gremlin types
  leak out.
* ``flatten_value_map`` lives here as a private helper; the public copy in
  ``dependencies.py`` is kept for backward-compat but delegates here.
* LRU caching for frequently-accessed vertices to reduce repeated queries.

Updated: 2026-03-23 - Added vertex caching for performance optimization
"""

import concurrent.futures
import logging
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from gremlin_python.process.graph_traversal import GraphTraversalSource, __
from gremlin_python.process.traversal import P, T

logger = logging.getLogger(__name__)


# Module-level cache for vertex lookups using proper LRU eviction
# Thread-safe implementation with hit/miss metrics
# Optimized with OrderedDict for O(1) operations (2026-04-08)
class _VertexCache:
    """Thread-safe LRU cache for vertex lookups with metrics tracking.
    
    Uses OrderedDict for O(1) access, insertion, and deletion operations.
    Maintains LRU order automatically with move_to_end().
    
    Performance:
        - get(): O(1) - OrderedDict lookup + move_to_end
        - set(): O(1) - OrderedDict insertion + optional popitem
        - invalidate(): O(1) - OrderedDict deletion
        - invalidate_pattern(): O(n) - Must scan all keys
    """
    
    def __init__(self, max_size: int = 1000):
        # Use OrderedDict for O(1) LRU operations
        self._cache: OrderedDict[Tuple[str, str], Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
        
        # Metrics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def get(self, key: Tuple[str, str]) -> Optional[Dict[str, Any]]:
        """Get vertex from cache, updating LRU order.
        
        Time Complexity: O(1)
        """
        with self._lock:
            if key in self._cache:
                # Move to end (most recently used) - O(1) operation
                self._cache.move_to_end(key)
                self._hits += 1
                logger.debug("Cache HIT for vertex: %s=%s", key[0], key[1])
                return self._cache[key]
            self._misses += 1
            return None
    
    def set(self, key: Tuple[str, str], value: Dict[str, Any]) -> None:
        """Set vertex in cache with LRU eviction.
        
        Time Complexity: O(1)
        """
        with self._lock:
            if key in self._cache:
                # Update existing, move to end - O(1) operation
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                # Evict least recently used if at capacity
                if len(self._cache) >= self._max_size:
                    # popitem(last=False) removes first (oldest) item - O(1)
                    lru_key, _ = self._cache.popitem(last=False)
                    self._evictions += 1
                    logger.debug("Evicted cached vertex (LRU): %s=%s", lru_key[0], lru_key[1])
                
                # Add new item at end - O(1)
                self._cache[key] = value
                logger.debug("Cache SET for vertex: %s=%s", key[0], key[1])
    
    def invalidate(self, key: Tuple[str, str]) -> bool:
        """Invalidate a specific cache entry.
        
        Time Complexity: O(1)
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]  # O(1) deletion in OrderedDict
                logger.debug("Invalidated cached vertex: %s=%s", key[0], key[1])
                return True
            return False
    
    def invalidate_pattern(self, id_field: str) -> int:
        """Invalidate all cache entries matching an id_field pattern.
        
        Time Complexity: O(n) - Must scan all keys
        """
        with self._lock:
            keys_to_remove = [k for k in self._cache if k[0] == id_field]
            for key in keys_to_remove:
                del self._cache[key]  # O(1) per deletion
            if keys_to_remove:
                logger.debug("Invalidated %d vertices with field: %s", len(keys_to_remove), id_field)
            return len(keys_to_remove)
    
    def clear(self) -> None:
        """Clear the entire cache.
        
        Time Complexity: O(1)
        """
        with self._lock:
            self._cache.clear()
            logger.info("Cleared vertex cache")
    
    def stats(self) -> Dict[str, Any]:
        """Return cache statistics including hit ratio.
        
        Time Complexity: O(1)
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = self._hits / total_requests if total_requests > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_ratio": round(hit_ratio, 4),
                "total_requests": total_requests,
            }
    
    def warm(self, entries: List[Tuple[Tuple[str, str], Dict[str, Any]]]) -> int:
        """Warm the cache with pre-fetched entries.
        
        Args:
            entries: List of (key, value) tuples to pre-populate cache.
        
        Returns:
            Number of entries added to cache.
        
        Time Complexity: O(n) where n is number of entries
        """
        with self._lock:
            added = 0
            for key, value in entries:
                if len(self._cache) >= self._max_size:
                    break
                if key not in self._cache:
                    self._cache[key] = value
                    added += 1
            if added > 0:
                logger.info("Warmed cache with %d entries", added)
            return added


# Global cache instance
_VERTEX_CACHE = _VertexCache(max_size=1000)


def _cache_get(id_field: str, id_value: str) -> Optional[Dict[str, Any]]:
    """Get vertex from cache if exists (backward-compatible wrapper)."""
    return _VERTEX_CACHE.get((id_field, id_value))


def _cache_set(id_field: str, id_value: str, vertex: Dict[str, Any]) -> None:
    """Set vertex in cache with LRU eviction (backward-compatible wrapper)."""
    _VERTEX_CACHE.set((id_field, id_value), vertex)


def _cache_invalidate(id_field: str, id_value: str) -> bool:
    """Invalidate a specific cache entry."""
    return _VERTEX_CACHE.invalidate((id_field, id_value))


def _cache_clear() -> None:
    """Clear the vertex cache."""
    _VERTEX_CACHE.clear()


def _cache_stats() -> Dict[str, Any]:
    """Return cache statistics with hit ratio."""
    return _VERTEX_CACHE.stats()


def _flatten_value_map(value_map: Dict) -> Dict:
    """Flatten JanusGraph ``valueMap(True)`` result.

    JanusGraph wraps every property value in a single-element list and uses
    ``T.id`` / ``T.label`` enum keys.  This helper normalises to plain
    ``{str: scalar}`` dicts.
    """
    flat: Dict[str, Any] = {}
    for key, value in value_map.items():
        if key == T.id:
            flat["id"] = value
        elif key == T.label:
            flat["label"] = value
        elif isinstance(value, list) and len(value) == 1:
            flat[key] = value[0]
        else:
            flat[key] = value
    return flat


class GraphRepository:
    """Typed facade over JanusGraph Gremlin traversals.

    Parameters
    ----------
    g : GraphTraversalSource
        A live traversal source (e.g. from ``get_graph_connection()``).
    """

    def __init__(self, g: GraphTraversalSource) -> None:
        """Initialize the repository with a graph traversal source.

        Args:
            g: A live Gremlin traversal source for executing queries.
        """
        self._g = g

    @property
    def g(self) -> GraphTraversalSource:
        """Return the underlying graph traversal source."""
        return self._g

    # ------------------------------------------------------------------
    # Health / stats
    # ------------------------------------------------------------------

    def vertex_count(self) -> int:
        """Return total number of vertices in the graph.

        Returns:
            Integer count of all vertices.
        """
        return self._g.V().count().next()

    def edge_count(self) -> int:
        """Return total number of edges in the graph.

        Returns:
            Integer count of all edges.
        """
        return self._g.E().count().next()

    def vertex_count_by_label(self, label: str) -> int:
        """Return count of vertices with a specific label.

        Args:
            label: Vertex label to filter by.

        Returns:
            Integer count of matching vertices.
        """
        return self._g.V().has_label(label).count().next()

    def graph_stats(self) -> Dict[str, int]:
        """Return aggregate statistics about the graph.

        Returns:
            Dictionary with vertex, edge, and label-specific counts.
        """
        return {
            "vertex_count": self.vertex_count(),
            "edge_count": self.edge_count(),
            "person_count": self.vertex_count_by_label("person"),
            "company_count": self.vertex_count_by_label("company"),
            "account_count": self.vertex_count_by_label("account"),
            "transaction_count": self.vertex_count_by_label("transaction"),
        }

    def health_check(self) -> bool:
        """Return ``True`` if a simple count query succeeds."""
        try:
            self._g.V().limit(1).count().next()
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Fraud detection
    # ------------------------------------------------------------------

    def find_shared_addresses(self, min_members: int = 3) -> List[Dict[str, Any]]:
        """Find addresses shared by >= *min_members* persons."""
        return self.find_shared_addresses_with_accounts(
            min_members=min_members, include_accounts=False
        )

    def find_shared_addresses_with_accounts(
        self, min_members: int = 3, include_accounts: bool = False
    ) -> List[Dict[str, Any]]:
        """Find shared addresses with optional per-member account enrichment."""
        if include_accounts:
            results = (
                self._g.V()
                .has_label("address")
                .where(__.in_("has_address").count().is_(P.gte(min_members)))
                .project("address_id", "city", "members")
                .by(__.values("address_id"))
                .by(__.values("city"))
                .by(
                    __.in_("has_address")
                    .project("person_id", "account_ids")
                    .by(__.values("person_id"))
                    .by(__.out("owns_account").values("account_id").fold())
                    .fold()
                )
                .toList()
            )
        else:
            results = (
                self._g.V()
                .has_label("address")
                .where(__.in_("has_address").count().is_(P.gte(min_members)))
                .project("address_id", "city", "persons")
                .by(__.values("address_id"))
                .by(__.values("city"))
                .by(__.in_("has_address").values("person_id").fold())
                .toList()
            )

        def _normalise_members(raw: Any) -> List[Dict[str, Any]]:
            if not include_accounts:
                return [{"person_id": member} for member in (raw or [])]
            return raw or []

        return [
            {
                "type": "shared_address",
                "indicator": r.get("address_id"),
                "location": r.get("city"),
                "members": (
                    r.get("persons", r.get("members", []))
                    if not include_accounts
                    else _normalise_members(r.get("members"))
                ),
                "members_simple": r.get("persons", r.get("members", [])),
                "member_count": len(r.get("persons", r.get("members", []))),
                "member_accounts": (
                    [entry.get("account_ids", []) for entry in _normalise_members(r.get("members"))]
                    if include_accounts
                    else []
                ),
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # AML structuring detection
    # ------------------------------------------------------------------

    def get_account_transaction_summaries(
        self, account_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return per-account transaction count and total for structuring analysis."""
        traversal = self._g.V().has_label("account")
        if account_id is not None:
            traversal = traversal.has("account_id", account_id)

        return (
            traversal.project("account_id", "holder", "txn_count", "total")
            .by(__.values("account_id"))
            .by(
                __.in_("owns_account").coalesce(
                    __.values("full_name"),
                    __.values("company_name"),
                    __.constant("Unknown"),
                )
            )
            .by(__.out_e("from_account").count())
            .by(__.out_e("from_account").in_v().values("amount").sum_())
            .toList()
        )

    # ------------------------------------------------------------------
    # UBO discovery
    # ------------------------------------------------------------------

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Return flattened company properties, or ``None`` if not found."""
        results = self._g.V().has("company_id", company_id).value_map(True).toList()
        if not results:
            return None
        return _flatten_value_map(results[0])

    def company_exists(self, company_id: str) -> bool:
        """Check if a company vertex exists.

        Args:
            company_id: The company identifier to check.

        Returns:
            True if company exists, False otherwise.
        """
        return self._g.V().has("company_id", company_id).hasNext()

    def find_direct_owners(self, company_id: str) -> List[Dict[str, Any]]:
        """Return direct beneficial owners with ownership percentage."""
        return (
            self._g.V()
            .has("company_id", company_id)
            .in_e("beneficial_owner")
            .project("person_id", "name", "ownership_percentage")
            .by(__.out_v().values("person_id"))
            .by(__.out_v().coalesce(__.values("full_name"), __.constant("Unknown")))
            .by(__.coalesce(__.values("ownership_percentage"), __.constant(0.0)))
            .toList()
        )

    def find_ubo_owners(
        self,
        company_id: str,
        ownership_threshold: float = 25.0,
        *,
        include_indirect: bool = True,
        max_depth: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int, bool]:
        """Discover UBOs with optional indirect traversal."""
        direct_owners = [
            owner
            for owner in self.find_direct_owners(company_id)
            if owner.get("ownership_percentage", 0.0) >= ownership_threshold
        ]

        for owner in direct_owners:
            owner["ownership_type"] = "direct"
            owner["chain_length"] = 1

        if not include_indirect:
            return direct_owners, 1 if direct_owners else 0, False

        # Import lazily to avoid introducing a hard dependency at module import.
        from src.python.analytics.ubo_discovery import UBODiscovery

        indirect_owners: List[Dict[str, Any]] = []
        try:
            discovery = UBODiscovery(ownership_threshold=ownership_threshold)
            discovery.g = self._g
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    discovery.find_ubos_for_company,
                    company_id=company_id,
                    include_indirect=True,
                    max_depth=max_depth,
                )
                result = future.result(timeout=15.0)
            for ubo in result.ubos:
                if ubo["chain_length"] <= 1:
                    continue
                indirect_owners.append(ubo)
        except concurrent.futures.TimeoutError:
            logger.debug("UBO discovery timed out after 15.0s; falling back to direct owners only")
            return direct_owners, 1 if direct_owners else 0, False
        except Exception as exc:
            logger.debug("Fallback to direct owners only: %s", exc)
            return direct_owners, 1 if direct_owners else 0, False

        # Deduplicate UBOs by person and keep the strongest chain.
        merged: Dict[str, Dict[str, Any]] = {owner["person_id"]: owner for owner in direct_owners}
        for owner in indirect_owners:
            current = merged.get(owner["person_id"])
            if current is None or owner["ownership_percentage"] > current.get(
                "ownership_percentage", 0.0
            ):
                merged[owner["person_id"]] = owner

        merged_owners = list(merged.values())
        total_layers = (
            max([1] + [owner.get("chain_length", 1) for owner in merged_owners])
            if merged_owners
            else 0
        )

        return merged_owners, total_layers, getattr(result, "has_circular_ownership", False)

    def get_owner_vertices(self, company_id: str) -> List[Dict[str, Any]]:
        """Return full valueMap of persons who own a company (for network view)."""
        raw = (
            self._g.V()
            .has("company_id", company_id)
            .in_e("beneficial_owner")
            .out_v()
            .value_map(True)
            .toList()
        )
        return [_flatten_value_map(r) for r in raw]

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    def get_vertex(self, id_field: str, id_value: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Return a single vertex by an indexed property, or ``None``.
        
        Args:
            id_field: The property name to search on (e.g., 'person_id', 'company_id')
            id_value: The property value to match
            use_cache: If True, check cache before querying (default: True)
        
        Returns:
            Flattened vertex dict or None if not found
        """
        # Check cache first
        if use_cache:
            cached = _cache_get(id_field, id_value)
            if cached is not None:
                logger.debug("Cache HIT for vertex: %s=%s", id_field, id_value)
                return cached
        
        # Query from graph
        results = self._g.V().has(id_field, id_value).value_map(True).toList()
        if not results:
            return None
        
        vertex = _flatten_value_map(results[0])
        
        # Cache the result
        if use_cache:
            _cache_set(id_field, id_value, vertex)
            logger.debug("Cache SET for vertex: %s=%s", id_field, id_value)
        
        return vertex

    def vertex_exists(self, id_field: str, id_value: str) -> bool:
        """Check if a vertex exists by property value.

        Args:
            id_field: Property name to search on.
            id_value: Property value to match.

        Returns:
            True if vertex exists, False otherwise.
        """
        return self._g.V().has(id_field, id_value).hasNext()

    @staticmethod
    def flatten_value_map(value_map: Dict) -> Dict:
        """Public access to value-map flattening (delegates to module helper)."""
        return _flatten_value_map(value_map)
    
    @staticmethod
    def cache_stats() -> Dict[str, Any]:
        """Return vertex cache statistics with hit ratio."""
        return _cache_stats()
    
    @staticmethod
    def cache_clear() -> None:
        """Clear the vertex cache."""
        _cache_clear()
    
    @staticmethod
    def cache_invalidate(id_field: str, id_value: str) -> bool:
        """Invalidate a specific cached vertex.
        
        Call this after mutating a vertex to ensure cache consistency.
        
        Args:
            id_field: The property name the vertex was cached under.
            id_value: The property value to invalidate.
        
        Returns:
            True if the entry was found and removed, False otherwise.
        """
        return _cache_invalidate(id_field, id_value)
    
    @staticmethod
    def cache_invalidate_pattern(id_field: str) -> int:
        """Invalidate all cached vertices matching an id_field pattern.
        
        Useful when a bulk operation affects all vertices of a certain type.
        
        Args:
            id_field: The property name pattern to match (e.g., 'person_id').
        
        Returns:
            Number of entries invalidated.
        """
        return _VERTEX_CACHE.invalidate_pattern(id_field)
    
    def invalidate_vertex(self, id_field: str, id_value: str) -> bool:
        """Invalidate a cached vertex after a mutation operation.
        
        This is an instance method convenience wrapper for cache_invalidate.
        Should be called after any create/update/delete operation on a vertex.
        
        Args:
            id_field: The property name the vertex was cached under.
            id_value: The property value to invalidate.
        
        Returns:
            True if the entry was found and removed, False otherwise.
        
        Example:
            >>> repo = GraphRepository(g)
            >>> # After updating a person vertex:
            >>> repo.invalidate_vertex('person_id', 'person-123')
        """
        return _cache_invalidate(id_field, id_value)
