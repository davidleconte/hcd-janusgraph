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

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-03
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from gremlin_python.driver import client, serializer

logger = logging.getLogger(__name__)


class JanusGraphLoader:
    """
    Loader for JanusGraph that creates vertices and edges from generated data.

    Supports:
    - Persons, Companies, Accounts, Transactions, Communications
    - Edge relationships: owns_account, sent_transaction, received_transaction,
      works_for, communicated_with, etc.
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
        # Test connection
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

    def load_persons(self, persons: List[Any]) -> Dict[str, int]:
        """
        Load person vertices into JanusGraph.

        Args:
            persons: List of Person objects from generator

        Returns:
            Mapping of person_id to JanusGraph vertex ID
        """
        logger.info("Loading %s persons...", len(persons))
        person_id_map = {}

        for i, person in enumerate(persons):
            # Extract person data
            person_dict = person.model_dump()
            person_id = person_dict.get("person_id") or person_dict.get("id")

            # Check if person already exists
            existing = self._submit(
                "g.V().has('person', 'person_id', pid).id()", {"pid": person_id}
            )

            if existing:
                person_id_map[person_id] = existing[0]
                continue

            # Create person vertex
            query = """
            g.addV('person')
                .property('person_id', pid)
                .property('first_name', fname)
                .property('last_name', lname)
                .property('date_of_birth', dob)
                .property('nationality', nationality)
                .property('risk_score', risk)
                .property('created_at', created)
                .id()
            """

            bindings = {
                "pid": person_id,
                "fname": person_dict.get("first_name", ""),
                "lname": person_dict.get("last_name", ""),
                "dob": str(person_dict.get("date_of_birth", "")),
                "nationality": person_dict.get("nationality", "US"),
                "risk": float(person_dict.get("risk_score", 0.0)),
                "created": datetime.now().isoformat(),
            }

            result = self._submit(query, bindings)
            if result:
                person_id_map[person_id] = result[0]
                self.stats["vertices_created"] += 1

            if (i + 1) % 50 == 0:
                logger.info("  Loaded %s/%s persons", i + 1, len(persons))

        logger.info("✓ Loaded %s persons", len(person_id_map))
        return person_id_map

    def load_companies(self, companies: List[Any]) -> Dict[str, int]:
        """
        Load company vertices into JanusGraph.

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

            # Check if company already exists
            existing = self._submit(
                "g.V().has('company', 'company_id', cid).id()", {"cid": company_id}
            )

            if existing:
                company_id_map[company_id] = existing[0]
                continue

            query = """
            g.addV('company')
                .property('company_id', cid)
                .property('name', cname)
                .property('industry', industry)
                .property('country', country)
                .property('risk_score', risk)
                .property('created_at', created)
                .id()
            """

            bindings = {
                "cid": company_id,
                "cname": company_dict.get("name", ""),
                "industry": company_dict.get("industry", "Unknown"),
                "country": company_dict.get("country", "US"),
                "risk": float(company_dict.get("risk_score", 0.0)),
                "created": datetime.now().isoformat(),
            }

            result = self._submit(query, bindings)
            if result:
                company_id_map[company_id] = result[0]
                self.stats["vertices_created"] += 1

        logger.info("✓ Loaded %s companies", len(company_id_map))
        return company_id_map

    def load_accounts(
        self, accounts: List[Any], person_id_map: Dict[str, int], company_id_map: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Load account vertices and create owns_account edges.

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

            # Check if account already exists
            existing = self._submit(
                "g.V().has('account', 'account_id', aid).id()", {"aid": account_id}
            )

            if existing:
                account_id_map[account_id] = existing[0]
                continue

            # Create account vertex
            query = """
            g.addV('account')
                .property('account_id', aid)
                .property('account_type', atype)
                .property('currency', currency)
                .property('balance', balance)
                .property('status', status)
                .property('opened_date', opened)
                .property('created_at', created)
                .id()
            """

            bindings = {
                "aid": account_id,
                "atype": account_dict.get("account_type", "checking"),
                "currency": account_dict.get("currency", "USD"),
                "balance": float(account_dict.get("balance", 0.0)),
                "status": account_dict.get("status", "active"),
                "opened": str(account_dict.get("opened_date", "")),
                "created": datetime.now().isoformat(),
            }

            result = self._submit(query, bindings)
            if result:
                account_vertex_id = result[0]
                account_id_map[account_id] = account_vertex_id
                self.stats["vertices_created"] += 1

                # Create owns_account edge
                owner_id = account_dict.get("owner_id")
                owner_type = account_dict.get("owner_type", "person")

                if owner_id:
                    if owner_type == "person" and owner_id in person_id_map:
                        owner_vertex_id = person_id_map[owner_id]
                        self._submit(
                            "g.addE('owns_account').from(__.V(oid)).to(__.V(aid)).property('since', since)",
                            {
                                "oid": owner_vertex_id,
                                "aid": account_vertex_id,
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
                                "aid": account_vertex_id,
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
        Load transaction vertices and create sent/received edges.

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

            # Check if transaction already exists
            existing = self._submit(
                "g.V().has('transaction', 'transaction_id', tid).id()", {"tid": tx_id}
            )

            if existing:
                transaction_id_map[tx_id] = existing[0]
                continue

            # Create transaction vertex
            query = """
            g.addV('transaction')
                .property('transaction_id', tid)
                .property('amount', amount)
                .property('currency', currency)
                .property('transaction_type', ttype)
                .property('timestamp', ts)
                .property('status', status)
                .property('is_suspicious', suspicious)
                .property('created_at', created)
                .id()
            """

            bindings = {
                "tid": tx_id,
                "amount": float(tx_dict.get("amount", 0.0)),
                "currency": tx_dict.get("currency", "USD"),
                "ttype": tx_dict.get("transaction_type", "transfer"),
                "ts": str(tx_dict.get("timestamp", "")),
                "status": tx_dict.get("status", "completed"),
                "suspicious": bool(tx_dict.get("is_suspicious", False)),
                "created": datetime.now().isoformat(),
            }

            result = self._submit(query, bindings)
            if result:
                tx_vertex_id = result[0]
                transaction_id_map[tx_id] = tx_vertex_id
                self.stats["vertices_created"] += 1

                # Create sent_transaction edge (from_account -> transaction)
                from_account_id = tx_dict.get("from_account_id")
                if from_account_id and from_account_id in account_id_map:
                    self._submit(
                        "g.addE('sent_transaction').from(__.V(fid)).to(__.V(tid)).property('timestamp', ts)",
                        {
                            "fid": account_id_map[from_account_id],
                            "tid": tx_vertex_id,
                            "ts": str(tx_dict.get("timestamp", "")),
                        },
                    )
                    self.stats["edges_created"] += 1

                # Create received_transaction edge (transaction -> to_account)
                to_account_id = tx_dict.get("to_account_id")
                if to_account_id and to_account_id in account_id_map:
                    self._submit(
                        "g.addE('received_by').from(__.V(tid)).to(__.V(toid)).property('timestamp', ts)",
                        {
                            "tid": tx_vertex_id,
                            "toid": account_id_map[to_account_id],
                            "ts": str(tx_dict.get("timestamp", "")),
                        },
                    )
                    self.stats["edges_created"] += 1

            if (i + 1) % 100 == 0:
                logger.info("  Loaded %s/%s transactions", i + 1, len(transactions))

        logger.info("✓ Loaded %s transactions with edges", len(transaction_id_map))
        return transaction_id_map

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
                "ts": str(trade_dict.get("trade_date", "")),
                "created": datetime.now().isoformat(),
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
                            "ts": str(comm_dict.get("timestamp", "")),
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
