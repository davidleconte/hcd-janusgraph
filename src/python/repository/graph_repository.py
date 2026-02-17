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



import logging
from typing import Any, Dict, List, Optional, Tuple

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
        return self._g.V().has_label(label).count().next()

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
        return self.find_shared_addresses_with_accounts(min_members=min_members, include_accounts=False)

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
                "member_accounts": [entry.get("account_ids", []) for entry in _normalise_members(r.get("members"))]
                if include_accounts
                else [],
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
        results = (
            self._g.V()
            .has("company_id", company_id)
            .value_map(True)
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
    ) -> Tuple[List[Dict[str, Any]], int]:
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
            return direct_owners, 1 if direct_owners else 0

        # Import lazily to avoid introducing a hard dependency at module import.
        from src.python.analytics.ubo_discovery import UBODiscovery

        indirect_owners: List[Dict[str, Any]] = []
        try:
            discovery = UBODiscovery(ownership_threshold=ownership_threshold)
            discovery.g = self._g
            result = discovery.find_ubos_for_company(
                company_id=company_id,
                include_indirect=True,
                max_depth=max_depth,
            )
            for ubo in result.ubos:
                if ubo["chain_length"] <= 1:
                    continue
                indirect_owners.append(ubo)
        except Exception as exc:
            logger.debug("Fallback to direct owners only: %s", exc)
            return direct_owners, 1 if direct_owners else 0

        # Deduplicate UBOs by person and keep the strongest chain.
        merged: Dict[str, Dict[str, Any]] = {
            owner["person_id"]: owner for owner in direct_owners
        }
        for owner in indirect_owners:
            current = merged.get(owner["person_id"])
            if current is None or owner["ownership_percentage"] > current.get(
                "ownership_percentage", 0.0
            ):
                merged[owner["person_id"]] = owner

        merged_owners = list(merged.values())
        total_layers = max(
            [1] + [owner.get("chain_length", 1) for owner in merged_owners]
        ) if merged_owners else 0

        return merged_owners, total_layers

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

    def get_vertex(self, id_field: str, id_value: str) -> Optional[Dict[str, Any]]:
        """Return a single vertex by an indexed property, or ``None``."""
        results = self._g.V().has(id_field, id_value).value_map(True).toList()
        if not results:
            return None
        return _flatten_value_map(results[0])

    def vertex_exists(self, id_field: str, id_value: str) -> bool:
        return self._g.V().has(id_field, id_value).hasNext()

    @staticmethod
    def flatten_value_map(value_map: Dict) -> Dict:
        """Public access to value-map flattening (delegates to module helper)."""
        return _flatten_value_map(value_map)
