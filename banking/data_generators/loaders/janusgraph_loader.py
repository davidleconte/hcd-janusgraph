"""
JanusGraph Data Loader
=======================

Loads synthetic data from MasterOrchestrator into JanusGraph with full
vertex and edge relationship support.

Features:
- Loads all entity types as vertices (person, company, account, transaction, etc.)
- Creates all edge relationships (owns_account, sent_transaction, etc.)
- Batch processing for performance
- Idempotent loading with duplicate detection
- Progress tracking and statistics

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-03
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)

REQUIRED_PERSON_FIELDS = {"person_id", "first_name", "last_name", "full_name", "nationality", "risk_level"}
REQUIRED_COMPANY_FIELDS = {"company_id", "legal_name", "registration_country"}
REQUIRED_ACCOUNT_FIELDS = {"account_id", "account_type", "currency"}
REQUIRED_TRANSACTION_FIELDS = {"transaction_id", "amount", "currency"}

SKIP_KEYS = {"updated_at", "entity_id", "version", "source", "metadata", "id"}


def _serialize_value(value: Any) -> Any:
    """Serialize a Python value for JanusGraph storage."""
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return int(value.timestamp())
    if isinstance(value, date):
        from calendar import timegm
        return timegm(value.timetuple())
    if isinstance(value, (list, dict)):
        import json
        return json.dumps(value, default=str)
    return str(value)


def _validate_entity(entity_dict: Dict[str, Any], required_fields: set, entity_type: str) -> List[str]:
    """Validate that required fields are present and non-empty."""
    missing = []
    for field in required_fields:
        val = entity_dict.get(field)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(field)
    if missing:
        logger.warning("Entity %s missing required fields: %s", entity_type, missing)
    return missing


class JanusGraphLoader:
    """
    Loader for JanusGraph that creates vertices and edges from generated data.

    Supports:
    - Persons, Companies, Accounts, Transactions, Communications
    - Edge relationships: owns_account, sent_transaction, received_transaction,
      works_for, communicated_with, etc.

    All entity properties are preserved during loading (no field stripping).
    Required fields are validated before insertion.
    """

    def __init__(self, url: str = "ws://localhost:18182/gremlin", traversal_source: str = "g"):
        """
        Initialize JanusGraph loader.

        Args:
            url: JanusGraph WebSocket URL
            traversal_source: Gremlin traversal source name
        """
        self.url = url
        self.traversal_source = traversal_source
        self.client = None
        self.stats = {
            "vertices_created": 0,
            "edges_created": 0,
            "errors": [],
            "start_time": None,
            "end_time": None,
        }

    def connect(self):
        """Establish connection to JanusGraph."""
        logger.info("Connecting to JanusGraph at %s...", self.url)
        self.client = client.Client(
            self.url, self.traversal_source, message_serializer=serializer.GraphSONSerializersV3d0()
        )
        result = self.client.submit("g.V().count()").all().result()
        logger.info("Connected. Current vertex count: %s", result[0])

    def close(self):
        """Close connection to JanusGraph."""
        if self.client:
            self.client.close()
            logger.info("Connection closed.")

    def _submit(self, query: str, bindings: Optional[Dict] = None) -> List[Any]:
        """Submit a Gremlin query with optional bindings."""
        try:
            if bindings:
                result = self.client.submit(query, bindings).all().result()
            else:
                result = self.client.submit(query).all().result()
            return result
        except Exception as e:
            logger.error("Query failed: %s... Error: %s", query[:100], e)
            self.stats["errors"].append(str(e))
            raise

    def clear_graph(self):
        """Clear all vertices and edges from the graph."""
        logger.warning("Clearing all graph data...")
        self._submit("g.V().drop().iterate()")
        logger.info("Graph cleared.")

    _MAX_BINDINGS = 14

    def _create_vertex(
        self, label: str, id_field: str, id_value: str, entity_dict: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Create a vertex with ALL properties from entity dict.

        Handles JanusGraph's binding limit by creating the vertex first,
        then updating remaining properties in batches.

        Args:
            label: Vertex label (e.g., 'person', 'account')
            id_field: ID property name (e.g., 'person_id')
            id_value: ID value
            entity_dict: Full entity dictionary from model_dump()

        Returns:
            Vertex ID if created, None otherwise
        """
        existing = self._submit(
            f"g.V().has('{label}', '{id_field}', pid).id()", {"pid": id_value}
        )
        if existing:
            return existing[0]

        all_props = []
        for key, value in entity_dict.items():
            if key in SKIP_KEYS or key == id_field:
                continue
            serialized = _serialize_value(value)
            if serialized is not None:
                all_props.append((key, serialized))


        chunks = []
        for i in range(0, len(all_props), self._MAX_BINDINGS):
            chunks.append(all_props[i:i + self._MAX_BINDINGS])

        if not chunks:
            chunks = [[]]

        first_chunk = chunks[0]
        bindings = {"pid": id_value}
        prop_strs = []
        for key, val in first_chunk:
            bk = f"p_{key}"[:50]
            bindings[bk] = val
            prop_strs.append(f".property('{key}', {bk})")

        props_joined = "\n                ".join(prop_strs)
        query = f"""
            g.addV('{label}')
                .property('{id_field}', pid)
                {props_joined}
                .id()
        """

        result = self._submit(query, bindings)
        if not result:
            return None

        vertex_id = result[0]
        self.stats["vertices_created"] += 1

        for chunk in chunks[1:]:
            bindings = {"vid": vertex_id}
            prop_strs = []
            for key, val in chunk:
                bk = f"p_{key}"[:50]
                bindings[bk] = val
                prop_strs.append(f".property('{key}', {bk})")
            props_joined = "\n                ".join(prop_strs)
            query = f"""
                g.V(vid)
                    {props_joined}
                    .id()
            """
            self._submit(query, bindings)

        return vertex_id

    def load_persons(self, persons: List[Any]) -> Dict[str, int]:
        """
        Load person vertices into JanusGraph with ALL properties.

        Validates required fields before insertion and preserves every
        property from the Person model.

        Args:
            persons: List of Person objects from generator

        Returns:
            Mapping of person_id to JanusGraph vertex ID
        """
        logger.info("Loading %s persons...", len(persons))
        person_id_map = {}

        for i, person in enumerate(persons):
            person_dict = person.model_dump()
            person_id = person_dict.get("person_id") or person_dict.get("id")

            if not person_id and person_dict.get("id"):
                person_id = person_dict["id"]
            if person_id:
                person_dict["person_id"] = person_id
            _validate_entity(person_dict, REQUIRED_PERSON_FIELDS, "person")
            if not person_id:
                logger.error("Skipping person: no person_id or id field")
                continue

            vertex_id = self._create_vertex("person", "person_id", person_id, person_dict)
            if vertex_id is not None:
                person_id_map[person_id] = vertex_id

            if (i + 1) % 50 == 0:
                logger.info("  Loaded %s/%s persons", i + 1, len(persons))

        logger.info("✓ Loaded %s persons", len(person_id_map))
        return person_id_map

    def load_companies(self, companies: List[Any]) -> Dict[str, int]:
        """
        Load company vertices into JanusGraph with ALL properties.

        Args:
            companies: List of Company objects from generator

        Returns:
            Mapping of company_id to JanusGraph vertex ID
        """
        logger.info("Loading %s companies...", len(companies))
        company_id_map = {}

        for i, company in enumerate(companies):
            company_dict = company.model_dump()
            company_id = company_dict.get("company_id") or company_dict.get("id")

            if not company_id and company_dict.get("id"):
                company_id = company_dict["id"]
            if company_id:
                company_dict["company_id"] = company_id
            _validate_entity(company_dict, REQUIRED_COMPANY_FIELDS, "company")
            if not company_id:
                logger.error("Skipping company: no company_id or id field")
                continue

            vertex_id = self._create_vertex("company", "company_id", company_id, company_dict)
            if vertex_id is not None:
                company_id_map[company_id] = vertex_id

        logger.info("✓ Loaded %s companies", len(company_id_map))
        return company_id_map

    def load_accounts(
        self, accounts: List[Any], person_id_map: Dict[str, int], company_id_map: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Load account vertices with ALL properties and create owns_account edges.

        Args:
            accounts: List of Account objects from generator
            person_id_map: Mapping of person_id to vertex ID
            company_id_map: Mapping of company_id to vertex ID

        Returns:
            Mapping of account_id to JanusGraph vertex ID
        """
        logger.info("Loading %s accounts...", len(accounts))
        account_id_map = {}

        for i, account in enumerate(accounts):
            account_dict = account.model_dump()
            account_id = account_dict.get("account_id") or account_dict.get("id")

            if not account_id and account_dict.get("id"):
                account_id = account_dict["id"]
            if account_id:
                account_dict["account_id"] = account_id
            _validate_entity(account_dict, REQUIRED_ACCOUNT_FIELDS, "account")
            if not account_id:
                logger.error("Skipping account: no account_id or id field")
                continue

            vertex_id = self._create_vertex("account", "account_id", account_id, account_dict)
            if vertex_id is not None:
                account_id_map[account_id] = vertex_id

                owner_id = account_dict.get("owner_id")
                owner_type = account_dict.get("owner_type", "person")

                if owner_id:
                    if owner_type == "person" and owner_id in person_id_map:
                        owner_vertex_id = person_id_map[owner_id]
                        self._submit(
                            "g.addE('owns_account').from(__.V(oid)).to(__.V(aid)).property('since', since)",
                            {
                                "oid": owner_vertex_id,
                                "aid": vertex_id,
                                "since": str(account_dict.get("opened_date", "")),
                            },
                        )
                        self.stats["edges_created"] += 1
                    elif owner_type == "company" and owner_id in company_id_map:
                        owner_vertex_id = company_id_map[owner_id]
                        self._submit(
                            "g.addE('owns_account').from(__.V(oid)).to(__.V(aid)).property('since', since)",
                            {
                                "oid": owner_vertex_id,
                                "aid": vertex_id,
                                "since": str(account_dict.get("opened_date", "")),
                            },
                        )
                        self.stats["edges_created"] += 1

            if (i + 1) % 50 == 0:
                logger.info("  Loaded %s/%s accounts", i + 1, len(accounts))

        logger.info("✓ Loaded %s accounts with ownership edges", len(account_id_map))
        return account_id_map

    def load_transactions(
        self, transactions: List[Any], account_id_map: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Load transaction vertices with ALL properties and create sent/received edges.

        Args:
            transactions: List of Transaction objects from generator
            account_id_map: Mapping of account_id to vertex ID

        Returns:
            Mapping of transaction_id to JanusGraph vertex ID
        """
        logger.info("Loading %s transactions...", len(transactions))
        transaction_id_map = {}

        for i, tx in enumerate(transactions):
            tx_dict = tx.model_dump()
            tx_id = tx_dict.get("transaction_id") or tx_dict.get("id")

            _validate_entity(tx_dict, REQUIRED_TRANSACTION_FIELDS, "transaction")
            if not tx_id and tx_dict.get("id"):
                tx_id = tx_dict["id"]
                tx_dict["transaction_id"] = tx_id
            if not tx_id:
                logger.error("Skipping transaction: no transaction_id or id field")
                continue

            vertex_id = self._create_vertex("transaction", "transaction_id", tx_id, tx_dict)
            if vertex_id is not None:
                transaction_id_map[tx_id] = vertex_id

                from_account_id = tx_dict.get("from_account_id")
                if from_account_id and from_account_id in account_id_map:
                    self._submit(
                        "g.addE('sent_transaction').from(__.V(fid)).to(__.V(tid)).property('timestamp', ts)",
                        {
                            "fid": account_id_map[from_account_id],
                            "tid": vertex_id,
                            "ts": _serialize_value(tx_dict.get("transaction_date")) or 0,
                        },
                    )
                    self.stats["edges_created"] += 1

                to_account_id = tx_dict.get("to_account_id")
                if to_account_id and to_account_id in account_id_map:
                    self._submit(
                        "g.addE('received_by').from(__.V(tid)).to(__.V(toid)).property('timestamp', ts)",
                        {
                            "tid": vertex_id,
                            "toid": account_id_map[to_account_id],
                            "ts": _serialize_value(tx_dict.get("transaction_date")) or 0,
                        },
                    )
                    self.stats["edges_created"] += 1

            if (i + 1) % 100 == 0:
                logger.info("  Loaded %s/%s transactions", i + 1, len(transactions))

        logger.info("✓ Loaded %s transactions with edges", len(transaction_id_map))
        return transaction_id_map


    def load_trades(
        self, trades: List[Any], account_id_map: Dict[str, int], person_id_map: Dict[str, int]
    ) -> int:
        """
        Load trade vertices and create edges.

        Args:
            trades: List of Trade objects
            account_id_map: Mapping of account_id to vertex ID
            person_id_map: Mapping of person_id to vertex ID

        Returns:
            Number of trades loaded
        """
        logger.info("Loading %s trades...", len(trades))
        trades_loaded = 0

        for i, trade in enumerate(trades):
            trade_dict = trade.model_dump()
            trade_id = trade_dict.get("trade_id") or trade_dict.get("id")

            # Check if trade already exists
            existing = self._submit("g.V().has('trade', 'trade_id', tid).id()", {"tid": trade_id})

            if existing:
                continue

            # Create trade vertex
            query = """
            g.addV('trade')
                .property('trade_id', tid)
                .property('symbol', symbol)
                .property('side', side)
                .property('quantity', qty)
                .property('price', price)
                .property('amount', amount)
                .property('timestamp', ts)
                .property('status', 'executed')
                .property('created_at', created)
                .id()
            """

            bindings = {
                "tid": trade_id,
                "symbol": trade_dict.get("symbol", ""),
                "side": trade_dict.get("side", "buy"),
                "qty": int(trade_dict.get("quantity", 0)),
                "price": float(trade_dict.get("price", 0.0)),
                "amount": float(trade_dict.get("total_value", 0.0)),
                "ts": _serialize_value(trade_dict.get("trade_date")) or 0,
                "created": _serialize_value(trade_dict.get("created_at")) or 0,
            }

            result = self._submit(query, bindings)
            if result:
                trade_vertex_id = result[0]
                self.stats["vertices_created"] += 1
                trades_loaded += 1

                # Link to Account (account -> executed_trade -> trade)
                acc_id = trade_dict.get("account_id")
                if acc_id and acc_id in account_id_map:
                    self._submit(
                        "g.addE('executed_trade').from(__.V(aid)).to(__.V(tid)).property('timestamp', ts)",
                        {
                            "aid": account_id_map[acc_id],
                            "tid": trade_vertex_id,
                            "ts": str(trade_dict.get("trade_date", "")),
                        },
                    )
                    self.stats["edges_created"] += 1

                # Link to Trader (person -> performed_trade -> trade)
                trader_id = trade_dict.get("trader_id")
                if trader_id and trader_id in person_id_map:
                    self._submit(
                        "g.addE('performed_trade').from(__.V(pid)).to(__.V(tid)).property('timestamp', ts)",
                        {
                            "pid": person_id_map[trader_id],
                            "tid": trade_vertex_id,
                            "ts": str(trade_dict.get("trade_date", "")),
                        },
                    )
                    self.stats["edges_created"] += 1

            if (i + 1) % 100 == 0:
                logger.info("  Loaded %s/%s trades", i + 1, len(trades))

        logger.info("✓ Loaded %s trades", trades_loaded)
        return trades_loaded

    def load_communications(self, communications: List[Any], person_id_map: Dict[str, int]) -> int:
        """
        Load communication edges between persons.

        Args:
            communications: List of Communication objects
            person_id_map: Mapping of person_id to vertex ID

        Returns:
            Number of communication edges created
        """
        logger.info("Loading %s communications...", len(communications))
        edges_created = 0

        for i, comm in enumerate(communications):
            comm_dict = comm.model_dump()

            from_id = comm_dict.get("from_person_id") or comm_dict.get("sender_id")
            # Handle recipient_ids as array (take first recipient)
            recipient_ids = comm_dict.get("recipient_ids", [])
            to_id = comm_dict.get("to_person_id") or comm_dict.get("recipient_id")
            if not to_id and recipient_ids:
                to_id = recipient_ids[0] if isinstance(recipient_ids, list) else recipient_ids

            if from_id and to_id:
                # Try to find vertices by person_id
                from_vertex = None
                to_vertex = None

                if from_id in person_id_map:
                    from_vertex = person_id_map[from_id]
                if to_id in person_id_map:
                    to_vertex = person_id_map[to_id]

                if from_vertex and to_vertex:
                    self._submit(
                        """g.addE('communicated_with')
                            .from(__.V(fid)).to(__.V(tid))
                            .property('comm_type', ctype)
                            .property('timestamp', ts)
                            .property('is_suspicious', suspicious)""",
                        {
                            "fid": from_vertex,
                            "tid": to_vertex,
                            "ctype": comm_dict.get("communication_type", "email"),
                            "ts": _serialize_value(comm_dict.get("timestamp")) or 0,
                            "suspicious": bool(comm_dict.get("is_suspicious", False)),
                        },
                    )
                    edges_created += 1
                    self.stats["edges_created"] += 1

            if (i + 1) % 100 == 0:
                logger.info("  Processed %s/%s communications", i + 1, len(communications))

        logger.info("✓ Created %s communication edges", edges_created)
        return edges_created

    def load_from_orchestrator(self, orchestrator: Any, clear_first: bool = False):
        """
        Load all data from a MasterOrchestrator instance.

        Args:
            orchestrator: MasterOrchestrator instance with generated data
            clear_first: Whether to clear the graph before loading
        """
        self.stats["start_time"] = datetime.now()

        try:
            self.connect()

            if clear_first:
                self.clear_graph()

            # Load in dependency order
            logger.info("\n" + "=" * 80)
            logger.info("Loading data into JanusGraph")
            logger.info("=" * 80)

            # 1. Load persons
            person_id_map = self.load_persons(orchestrator.persons)

            # 2. Load companies
            company_id_map = self.load_companies(orchestrator.companies)

            # 3. Load accounts with ownership edges
            account_id_map = self.load_accounts(
                orchestrator.accounts, person_id_map, company_id_map
            )

            # 4. Load transactions with edges
            self.load_transactions(orchestrator.transactions, account_id_map)

            # 5. Load communications as edges
            self.load_communications(orchestrator.communications, person_id_map)

            # 4.5 Load trades
            self.load_trades(orchestrator.trades, account_id_map, person_id_map)
            self.stats["end_time"] = datetime.now()

            # Print summary
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            logger.info("\n" + "=" * 80)
            logger.info("LOADING COMPLETE")
            logger.info("=" * 80)
            logger.info("Vertices created: %s", self.stats["vertices_created"])
            logger.info("Edges created: %s", self.stats["edges_created"])
            logger.info("Duration: %.2fs", duration)
            logger.info("Errors: %s", len(self.stats["errors"]))
            logger.info("=" * 80)

        finally:
            self.close()

        return self.stats


def generate_and_load(
    seed: int = 42,
    person_count: int = 50,
    company_count: int = 10,
    account_count: int = 100,
    transaction_count: int = 500,
    communication_count: int = 200,
    insider_trading_count: int = 0,
    tbml_count: int = 0,
    fraud_ring_count: int = 0,
    structuring_count: int = 0,
    clear_graph: bool = True,
    janusgraph_url: str = "ws://localhost:18182/gremlin",
) -> Dict[str, Any]:
    """
    Generate synthetic data and load into JanusGraph.

    This is a convenience function that combines MasterOrchestrator
    generation with JanusGraph loading.

    Args:
        seed: Random seed for reproducibility
        person_count: Number of persons to generate
        company_count: Number of companies to generate
        account_count: Number of accounts to generate
        transaction_count: Number of transactions to generate
        communication_count: Number of communications to generate
        insider_trading_count: Number of insider trading patterns
        tbml_count: Number of TBML patterns
        fraud_ring_count: Number of fraud ring patterns
        structuring_count: Number of structuring patterns
        clear_graph: Whether to clear existing graph data
        janusgraph_url: JanusGraph WebSocket URL

    Returns:
        Dictionary with generation and loading statistics
    """
    import sys
    from pathlib import Path

    # Add parent paths for imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

    from banking.data_generators.orchestration.master_orchestrator import (
        GenerationConfig,
        MasterOrchestrator,
    )

    # Configure generation
    config = GenerationConfig(
        seed=seed,
        person_count=person_count,
        company_count=company_count,
        account_count=account_count,
        transaction_count=transaction_count,
        communication_count=communication_count,
        # Pattern configurations
        insider_trading_patterns=insider_trading_count,
        tbml_patterns=tbml_count,
        fraud_ring_patterns=fraud_ring_count,
        structuring_patterns=structuring_count,
        trade_count=0,  # Skip trades for now
        travel_count=0,  # Skip travel for now
        document_count=0,  # Skip documents for now
        output_dir=Path("./output/janusgraph_load"),
    )

    # Generate data
    logger.info("=" * 80)
    logger.info("PHASE 1: GENERATING SYNTHETIC DATA")
    logger.info("=" * 80)

    orchestrator = MasterOrchestrator(config)
    gen_stats = orchestrator.generate_all()

    # Load into JanusGraph
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: LOADING INTO JANUSGRAPH")
    logger.info("=" * 80)

    loader = JanusGraphLoader(url=janusgraph_url)
    load_stats = loader.load_from_orchestrator(orchestrator, clear_first=clear_graph)

    return {
        "generation": {
            "persons": gen_stats.persons_generated,
            "companies": gen_stats.companies_generated,
            "accounts": gen_stats.accounts_generated,
            "transactions": gen_stats.transactions_generated,
            "communications": gen_stats.communications_generated,
            "total": gen_stats.total_records,
            "duration_seconds": gen_stats.generation_time_seconds,
        },
        "loading": load_stats,
    }


if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Generate and load data into JanusGraph")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--persons", type=int, default=50, help="Number of persons")
    parser.add_argument("--companies", type=int, default=10, help="Number of companies")
    parser.add_argument("--accounts", type=int, default=100, help="Number of accounts")
    parser.add_argument("--transactions", type=int, default=500, help="Number of transactions")
    parser.add_argument("--communications", type=int, default=200, help="Number of communications")
    # Pattern arguments
    parser.add_argument(
        "--insider-trading", type=int, default=0, help="Number of insider trading patterns"
    )
    parser.add_argument("--tbml", type=int, default=0, help="Number of TBML patterns")
    parser.add_argument("--fraud-ring", type=int, default=0, help="Number of fraud ring patterns")
    parser.add_argument("--structuring", type=int, default=0, help="Number of structuring patterns")

    parser.add_argument("--url", default="ws://localhost:18182/gremlin", help="JanusGraph URL")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear existing data")

    args = parser.parse_args()

    stats = generate_and_load(
        seed=args.seed,
        person_count=args.persons,
        company_count=args.companies,
        account_count=args.accounts,
        transaction_count=args.transactions,
        communication_count=args.communications,
        insider_trading_count=args.insider_trading,
        tbml_count=args.tbml,
        fraud_ring_count=args.fraud_ring,
        structuring_count=args.structuring,
        clear_graph=not args.no_clear,
        janusgraph_url=args.url,
    )

    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"Generated: {stats['generation']['total']} records")
    print(
        f"Loaded: {stats['loading']['vertices_created']} vertices, {stats['loading']['edges_created']} edges"
    )
    print("=" * 80)
