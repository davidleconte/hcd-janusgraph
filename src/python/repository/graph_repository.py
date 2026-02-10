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
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from gremlin_python.process.graph_traversal import GraphTraversalSource, __
from gremlin_python.process.traversal import P, T

logger = logging.getLogger(__name__)


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
        self._g = g

    @property
    def g(self) -> GraphTraversalSource:
        return self._g

    # ------------------------------------------------------------------
    # Health / stats
    # ------------------------------------------------------------------

    def vertex_count(self) -> int:
        return self._g.V().count().next()

    def edge_count(self) -> int:
        return self._g.E().count().next()

    def vertex_count_by_label(self, label: str) -> int:
        return self._g.V().hasLabel(label).count().next()

    def graph_stats(self) -> Dict[str, int]:
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
        results = (
            self._g.V()
            .hasLabel("address")
            .where(__.in_("has_address").count().is_(P.gte(min_members)))
            .project("address_id", "city", "persons")
            .by(__.values("address_id"))
            .by(__.values("city"))
            .by(__.in_("has_address").values("person_id").fold())
            .toList()
        )
        return [
            {
                "type": "shared_address",
                "indicator": r.get("address_id"),
                "location": r.get("city"),
                "members": r.get("persons", []),
                "member_count": len(r.get("persons", [])),
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # AML structuring detection
    # ------------------------------------------------------------------

    def get_account_transaction_summaries(self) -> List[Dict[str, Any]]:
        """Return per-account transaction count and total for structuring analysis."""
        return (
            self._g.V()
            .hasLabel("account")
            .project("account_id", "holder", "txn_count", "total")
            .by(__.values("account_id"))
            .by(
                __.in_("owns_account").coalesce(
                    __.values("full_name"),
                    __.values("company_name"),
                    __.constant("Unknown"),
                )
            )
            .by(__.outE("from_account").count())
            .by(__.outE("from_account").inV().values("amount").sum())
            .toList()
        )

    # ------------------------------------------------------------------
    # UBO discovery
    # ------------------------------------------------------------------

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Return flattened company properties, or ``None`` if not found."""
        results = (
            self._g.V()
            .has("company_id", company_id)
            .valueMap(True)
            .toList()
        )
        if not results:
            return None
        return _flatten_value_map(results[0])

    def company_exists(self, company_id: str) -> bool:
        return self._g.V().has("company_id", company_id).hasNext()

    def find_direct_owners(self, company_id: str) -> List[Dict[str, Any]]:
        """Return direct beneficial owners with ownership percentage."""
        return (
            self._g.V()
            .has("company_id", company_id)
            .inE("beneficial_owner")
            .project("person_id", "name", "ownership_percentage")
            .by(__.outV().values("person_id"))
            .by(__.outV().coalesce(__.values("full_name"), __.constant("Unknown")))
            .by(__.coalesce(__.values("ownership_percentage"), __.constant(0.0)))
            .toList()
        )

    def get_owner_vertices(self, company_id: str) -> List[Dict[str, Any]]:
        """Return full valueMap of persons who own a company (for network view)."""
        raw = (
            self._g.V()
            .has("company_id", company_id)
            .inE("beneficial_owner")
            .outV()
            .valueMap(True)
            .toList()
        )
        return [_flatten_value_map(r) for r in raw]

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    def get_vertex(self, id_field: str, id_value: str) -> Optional[Dict[str, Any]]:
        """Return a single vertex by an indexed property, or ``None``."""
        results = self._g.V().has(id_field, id_value).valueMap(True).toList()
        if not results:
            return None
        return _flatten_value_map(results[0])

    def vertex_exists(self, id_field: str, id_value: str) -> bool:
        return self._g.V().has(id_field, id_value).hasNext()

    @staticmethod
    def flatten_value_map(value_map: Dict) -> Dict:
        """Public access to value-map flattening (delegates to module helper)."""
        return _flatten_value_map(value_map)
