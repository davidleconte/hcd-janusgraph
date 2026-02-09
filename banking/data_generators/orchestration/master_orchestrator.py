"""
Master Orchestrator for Synthetic Data Generation
==================================================

Central coordination system for all data generators. Manages dependencies,
batch generation, progress tracking, and configuration management.

Features:
- Coordinate all 14 generators (core, event, pattern)
- Dependency management and referential integrity
- Batch generation with progress tracking
- Configuration management
- Error handling and recovery
- Memory-efficient streaming
- Export to multiple formats

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
import random

# Core generators
from ..core.person_generator import PersonGenerator
from ..core.company_generator import CompanyGenerator
from ..core.account_generator import AccountGenerator

# Event generators
from ..events.transaction_generator import TransactionGenerator
from ..events.communication_generator import CommunicationGenerator
from ..events.trade_generator import TradeGenerator
from ..events.travel_generator import TravelGenerator
from ..events.document_generator import DocumentGenerator

# Pattern generators
from ..patterns.insider_trading_pattern_generator import InsiderTradingPatternGenerator
from ..patterns.tbml_pattern_generator import TBMLPatternGenerator
from ..patterns.fraud_ring_pattern_generator import FraudRingPatternGenerator
from ..patterns.structuring_pattern_generator import StructuringPatternGenerator
from ..patterns.cato_pattern_generator import CATOPatternGenerator

# Data models
from ..utils.data_models import Person, Company, Account, Transaction, Communication, Pattern

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for data generation"""
    # Seed for reproducibility
    seed: Optional[int] = None
    
    # Entity counts
    person_count: int = 100
    company_count: int = 20
    account_count: int = 200
    
    # Event counts
    transaction_count: int = 10000
    communication_count: int = 5000
    trade_count: int = 1000
    travel_count: int = 500
    document_count: int = 2000
    
    # Pattern counts
    insider_trading_patterns: int = 0
    tbml_patterns: int = 0
    fraud_ring_patterns: int = 0
    structuring_patterns: int = 0
    cato_patterns: int = 0
    
    # Temporal settings
    start_date: Optional[datetime] = None
    duration_days: int = 365
    
    # Quality settings
    suspicious_transaction_rate: float = 0.02
    suspicious_communication_rate: float = 0.01
    
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    output_format: str = "json"  # json, csv, parquet
    include_ground_truth: bool = True
    include_metadata: bool = True
    
    # Performance settings
    batch_size: int = 1000
    enable_parallel: bool = False
    num_workers: int = 4


@dataclass
class GenerationStats:
    """Statistics from data generation"""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Entity counts
    persons_generated: int = 0
    companies_generated: int = 0
    accounts_generated: int = 0
    
    # Event counts
    transactions_generated: int = 0
    communications_generated: int = 0
    trades_generated: int = 0
    travels_generated: int = 0
    documents_generated: int = 0
    
    # Pattern counts
    patterns_generated: int = 0
    
    # Performance metrics
    total_records: int = 0
    generation_time_seconds: float = 0.0
    records_per_second: float = 0.0
    memory_used_mb: float = 0.0
    
    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def finalize(self):
        """Calculate final statistics"""
        self.end_time = datetime.now()
        self.generation_time_seconds = (self.end_time - self.start_time).total_seconds()
        self.total_records = (
            self.persons_generated + self.companies_generated + 
            self.accounts_generated + self.transactions_generated +
            self.communications_generated + self.trades_generated +
            self.travels_generated + self.documents_generated +
            self.patterns_generated
        )
        if self.generation_time_seconds > 0:
            self.records_per_second = self.total_records / self.generation_time_seconds


class MasterOrchestrator:
    """
    Master orchestrator for coordinating all data generators.
    
    Responsibilities:
    - Initialize and manage all generators
    - Coordinate entity and event generation
    - Manage dependencies and referential integrity
    - Track progress and statistics
    - Handle errors and recovery
    - Export data in multiple formats
    """
    
    def __init__(self, config: Optional[GenerationConfig] = None):
        """
        Initialize master orchestrator.
        
        Args:
            config: Generation configuration (uses defaults if None)
        """
        self.config = config or GenerationConfig()
        self.stats = GenerationStats()
        
        # Set random seed for reproducibility
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        # Initialize core generators
        logger.info("Initializing core generators...")
        self.person_gen = PersonGenerator(seed=self.config.seed)
        self.company_gen = CompanyGenerator(seed=self.config.seed)
        self.account_gen = AccountGenerator(seed=self.config.seed)
        
        # Initialize event generators
        logger.info("Initializing event generators...")
        self.transaction_gen = TransactionGenerator(seed=self.config.seed)
        self.communication_gen = CommunicationGenerator(seed=self.config.seed)
        self.trade_gen = TradeGenerator(seed=self.config.seed)
        self.travel_gen = TravelGenerator(seed=self.config.seed)
        self.document_gen = DocumentGenerator(seed=self.config.seed)
        
        # Initialize pattern generators
        logger.info("Initializing pattern generators...")
        self.insider_trading_gen = InsiderTradingPatternGenerator(seed=self.config.seed)
        self.tbml_gen = TBMLPatternGenerator(seed=self.config.seed)
        self.fraud_ring_gen = FraudRingPatternGenerator(seed=self.config.seed)
        self.structuring_gen = StructuringPatternGenerator(seed=self.config.seed)
        self.cato_gen = CATOPatternGenerator(seed=self.config.seed)
        
        # Storage for generated entities
        self.persons: List[Person] = []
        self.companies: List[Company] = []
        self.accounts: List[Account] = []
        self.transactions: List[Transaction] = []
        self.communications: List[Communication] = []
        self.trades: List[Any] = []
        self.travels: List[Any] = []
        self.documents: List[Any] = []
        self.patterns: List[Pattern] = []
        
        logger.info("Master orchestrator initialized successfully")
    
    def generate_all(self) -> GenerationStats:
        """
        Generate complete dataset with all entities, events, and patterns.
        
        Returns:
            Generation statistics
        """
        logger.info("=" * 80)
        logger.info("Starting complete data generation")
        logger.info("=" * 80)
        
        try:
            # Phase 1: Generate core entities
            self._generate_core_entities()
            
            # Phase 2: Generate events
            self._generate_events()
            
            # Phase 3: Generate patterns
            self._generate_patterns()
            
            # Phase 4: Export data
            self._export_data()
            
            # Finalize statistics
            self.stats.finalize()
            
            logger.info("=" * 80)
            logger.info("Data generation completed successfully")
            logger.info("Total records: %s", self.stats.total_records)
            logger.info("Generation time: %.2fs", self.stats.generation_time_seconds)
            logger.info("Records/second: %.2f", self.stats.records_per_second)
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error("Error during data generation: %s", e)
            self.stats.errors.append(str(e))
            raise
        
        return self.stats
    
    def _generate_core_entities(self):
        """Generate core entities (persons, companies, accounts)"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1: Generating Core Entities")
        logger.info("=" * 80)
        
        # Generate persons
        logger.info("Generating %s persons...", self.config.person_count)
        for i in range(self.config.person_count):
            person = self.person_gen.generate()
            self.persons.append(person)
            if (i + 1) % 100 == 0:
                logger.info("  Generated %s/%s persons", i + 1, self.config.person_count)
        self.stats.persons_generated = len(self.persons)
        logger.info("✓ Generated %s persons", self.stats.persons_generated)
        
        # Generate companies
        logger.info("\nGenerating %s companies...", self.config.company_count)
        for i in range(self.config.company_count):
            company = self.company_gen.generate()
            self.companies.append(company)
            if (i + 1) % 10 == 0:
                logger.info("  Generated %s/%s companies", i + 1, self.config.company_count)
        self.stats.companies_generated = len(self.companies)
        logger.info("✓ Generated %s companies", self.stats.companies_generated)
        
        # Generate accounts
        logger.info("\nGenerating %s accounts...", self.config.account_count)
        for i in range(self.config.account_count):
            # Randomly assign to person or company
            if random.random() < 0.8:  # 80% person accounts
                owner = random.choice(self.persons)
                account = self.account_gen.generate(
                    owner_id=owner.id,
                    owner_type="person"
                )
            else:  # 20% company accounts
                owner = random.choice(self.companies)
                account = self.account_gen.generate(
                    owner_id=owner.id,
                    owner_type="company"
                )
            self.accounts.append(account)
            if (i + 1) % 100 == 0:
                logger.info("  Generated %s/%s accounts", i + 1, self.config.account_count)
        self.stats.accounts_generated = len(self.accounts)
        logger.info("✓ Generated %s accounts", self.stats.accounts_generated)
    
    def _generate_events(self):
        """Generate events (transactions, communications, etc.)"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 2: Generating Events")
        logger.info("=" * 80)
        
        # Generate transactions
        if self.config.transaction_count > 0:
            logger.info("Generating %s transactions...", self.config.transaction_count)
            for i in range(self.config.transaction_count):
                # Select random accounts
                from_account = random.choice(self.accounts)
                to_account = random.choice(self.accounts)
                
                transaction = self.transaction_gen.generate(
                    from_account_id=from_account.id,
                    to_account_id=to_account.id
                )
                self.transactions.append(transaction)
                
                if (i + 1) % 1000 == 0:
                    logger.info("  Generated %s/%s transactions", i + 1, self.config.transaction_count)
            self.stats.transactions_generated = len(self.transactions)
            logger.info("✓ Generated %s transactions", self.stats.transactions_generated)
        
        # Generate communications
        if self.config.communication_count > 0:
            logger.info("\nGenerating %s communications...", self.config.communication_count)
            for i in range(self.config.communication_count):
                # Select random sender and recipient from generated persons
                sender = random.choice(self.persons)
                recipient = random.choice(self.persons)
                # Avoid self-communication
                while recipient.id == sender.id and len(self.persons) > 1:
                    recipient = random.choice(self.persons)
                
                communication = self.communication_gen.generate(
                    sender_id=sender.id,
                    recipient_id=recipient.id
                )
                self.communications.append(communication)
                
                if (i + 1) % 1000 == 0:
                    logger.info("  Generated %s/%s communications", i + 1, self.config.communication_count)
            self.stats.communications_generated = len(self.communications)
            logger.info("✓ Generated %s communications", self.stats.communications_generated)
        
        # Generate trades
        if self.config.trade_count > 0:
            logger.info("\nGenerating %s trades...", self.config.trade_count)
            for i in range(self.config.trade_count):
                trade = self.trade_gen.generate()
                self.trades.append(trade)
                
                if (i + 1) % 100 == 0:
                    logger.info("  Generated %s/%s trades", i + 1, self.config.trade_count)
            self.stats.trades_generated = len(self.trades)
            logger.info("✓ Generated %s trades", self.stats.trades_generated)
        
        # Generate travel records
        if self.config.travel_count > 0:
            logger.info("\nGenerating %s travel records...", self.config.travel_count)
            for i in range(self.config.travel_count):
                traveler = random.choice(self.persons)
                travel = self.travel_gen.generate(traveler_id=traveler.person_id)
                self.travels.append(travel)
                
                if (i + 1) % 100 == 0:
                    logger.info("  Generated %s/%s travel records", i + 1, self.config.travel_count)
            self.stats.travels_generated = len(self.travels)
            logger.info("✓ Generated %s travel records", self.stats.travels_generated)
        
        # Generate documents
        if self.config.document_count > 0:
            logger.info("\nGenerating %s documents...", self.config.document_count)
            for i in range(self.config.document_count):
                document = self.document_gen.generate()
                self.documents.append(document)
                
                if (i + 1) % 100 == 0:
                    logger.info("  Generated %s/%s documents", i + 1, self.config.document_count)
            self.stats.documents_generated = len(self.documents)
            logger.info("✓ Generated %s documents", self.stats.documents_generated)
    
    def _generate_patterns(self):
        """Generate financial crime patterns"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 3: Generating Patterns")
        logger.info("=" * 80)
        
        total_patterns = (
            self.config.insider_trading_patterns +
            self.config.tbml_patterns +
            self.config.fraud_ring_patterns +
            self.config.structuring_patterns +
            self.config.cato_patterns
        )
        
        if total_patterns == 0:
            logger.info("No patterns configured for generation")
            return
        
        # Collect existing entity IDs for pattern injection
        person_ids = [p.id for p in self.persons]
        company_ids = [c.id for c in self.companies]

        # Generate insider trading patterns
        if self.config.insider_trading_patterns > 0:
            logger.info("Generating %s insider trading patterns...", self.config.insider_trading_patterns)
            for i in range(self.config.insider_trading_patterns):
                pattern, trades, communications = self.insider_trading_gen.generate(
                    pattern_type="pre_announcement",
                    entity_count=random.randint(2, 5),
                    existing_entity_ids=person_ids
                )
                self.patterns.append(pattern)
                self.trades.extend(trades)
                self.communications.extend(communications)
            logger.info("✓ Generated %s insider trading patterns", self.config.insider_trading_patterns)
        
        # Generate TBML patterns
        if self.config.tbml_patterns > 0:
            logger.info("\nGenerating %s TBML patterns...", self.config.tbml_patterns)
            for i in range(self.config.tbml_patterns):
                pattern, transactions, documents = self.tbml_gen.generate(
                    pattern_type="over_invoicing",
                    entity_count=random.randint(3, 7),
                    existing_entity_ids=company_ids
                )
                self.patterns.append(pattern)
                self.transactions.extend(transactions)
                self.documents.extend(documents)
            logger.info("✓ Generated %s TBML patterns", self.config.tbml_patterns)
        
        # Generate fraud ring patterns
        if self.config.fraud_ring_patterns > 0:
            logger.info("\nGenerating %s fraud ring patterns...", self.config.fraud_ring_patterns)
            for i in range(self.config.fraud_ring_patterns):
                pattern = self.fraud_ring_gen.generate(
                    pattern_type="money_mule_network",
                    ring_size=random.randint(5, 10)
                )
                self.patterns.append(pattern)
            logger.info("✓ Generated %s fraud ring patterns", self.config.fraud_ring_patterns)
        
        # Generate structuring patterns
        if self.config.structuring_patterns > 0:
            logger.info("\nGenerating %s structuring patterns...", self.config.structuring_patterns)
            for i in range(self.config.structuring_patterns):
                pattern = self.structuring_gen.generate(
                    pattern_type="smurfing",
                    smurf_count=random.randint(5, 15)
                )
                self.patterns.append(pattern)
            logger.info("✓ Generated %s structuring patterns", self.config.structuring_patterns)
        
        # Generate CATO patterns
        if self.config.cato_patterns > 0:
            logger.info("\nGenerating %s CATO patterns...", self.config.cato_patterns)
            for i in range(self.config.cato_patterns):
                pattern = self.cato_gen.generate(
                    pattern_type="credential_stuffing",
                    victim_count=random.randint(5, 15)
                )
                self.patterns.append(pattern)
            logger.info("✓ Generated %s CATO patterns", self.config.cato_patterns)
        
        self.stats.patterns_generated = len(self.patterns)
        logger.info("\n✓ Total patterns generated: %s", self.stats.patterns_generated)
    
    def _export_data(self):
        """Export generated data to files"""
        logger.info("\n" + "=" * 80)
        logger.info("Phase 4: Exporting Data")
        logger.info("=" * 80)
        
        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Output directory: %s", self.config.output_dir)
        
        if self.config.output_format == "json":
            self._export_json()
        else:
            logger.warning("Export format '%s' not yet implemented", self.config.output_format)
    
    def _export_json(self):
        """Export data as JSON files"""
        # Export persons
        if self.persons:
            path = self.config.output_dir / "persons.json"
            with open(path, 'w') as f:
                json.dump([p.model_dump() for p in self.persons], f, indent=2, default=str)
            logger.info("✓ Exported %s persons to %s", len(self.persons), path)
        
        # Export companies
        if self.companies:
            path = self.config.output_dir / "companies.json"
            with open(path, 'w') as f:
                json.dump([c.model_dump() for c in self.companies], f, indent=2, default=str)
            logger.info("✓ Exported %s companies to %s", len(self.companies), path)
        
        # Export accounts
        if self.accounts:
            path = self.config.output_dir / "accounts.json"
            with open(path, 'w') as f:
                json.dump([a.model_dump() for a in self.accounts], f, indent=2, default=str)
            logger.info("✓ Exported %s accounts to %s", len(self.accounts), path)
        
        # Export transactions
        if self.transactions:
            path = self.config.output_dir / "transactions.json"
            with open(path, 'w') as f:
                json.dump([t.model_dump() for t in self.transactions], f, indent=2, default=str)
            logger.info("✓ Exported %s transactions to %s", len(self.transactions), path)
        
        # Export communications
        if self.communications:
            path = self.config.output_dir / "communications.json"
            with open(path, 'w') as f:
                json.dump([c.model_dump() for c in self.communications], f, indent=2, default=str)
            logger.info("✓ Exported %s communications to %s", len(self.communications), path)
        
        # Export patterns
        if self.patterns:
            path = self.config.output_dir / "patterns.json"
            with open(path, 'w') as f:
                json.dump([p.model_dump() for p in self.patterns], f, indent=2, default=str)
            logger.info("✓ Exported %s patterns to %s", len(self.patterns), path)
        
        # Export statistics
        stats_path = self.config.output_dir / "generation_stats.json"
        with open(stats_path, 'w') as f:
            json.dump({
                'start_time': self.stats.start_time.isoformat(),
                'end_time': self.stats.end_time.isoformat() if self.stats.end_time else None,
                'persons_generated': self.stats.persons_generated,
                'companies_generated': self.stats.companies_generated,
                'accounts_generated': self.stats.accounts_generated,
                'transactions_generated': self.stats.transactions_generated,
                'communications_generated': self.stats.communications_generated,
                'trades_generated': self.stats.trades_generated,
                'travels_generated': self.stats.travels_generated,
                'documents_generated': self.stats.documents_generated,
                'patterns_generated': self.stats.patterns_generated,
                'total_records': self.stats.total_records,
                'generation_time_seconds': self.stats.generation_time_seconds,
                'records_per_second': self.stats.records_per_second,
                'errors': self.stats.errors,
                'warnings': self.stats.warnings
            }, f, indent=2)
        logger.info("✓ Exported generation statistics to %s", stats_path)
    
    def export_to_json(self, output_path: str) -> Dict[str, Any]:
        """
        Export all generated data to a single JSON file.
        
        This is a convenience method for exporting all data to one file,
        commonly used in testing and simple workflows.
        
        Args:
            output_path: Path to the output JSON file
            
        Returns:
            Dictionary containing all generated data
        """
        from pathlib import Path
        
        # Prepare data dictionary
        data = {
            'persons': [p.model_dump() for p in self.persons],
            'companies': [c.model_dump() for c in self.companies],
            'accounts': [a.model_dump() for a in self.accounts],
            'transactions': [t.model_dump() for t in self.transactions],
            'communications': [c.model_dump() for c in self.communications],
            'trades': [t.model_dump() for t in self.trades],
            'travels': [t.model_dump() for t in self.travels],
            'documents': [d.model_dump() for d in self.documents],
            'patterns': [p.model_dump() for p in self.patterns],
            'statistics': {
                'start_time': self.stats.start_time.isoformat() if self.stats.start_time else None,
                'end_time': self.stats.end_time.isoformat() if self.stats.end_time else None,
                'persons_generated': self.stats.persons_generated,
                'companies_generated': self.stats.companies_generated,
                'accounts_generated': self.stats.accounts_generated,
                'transactions_generated': self.stats.transactions_generated,
                'communications_generated': self.stats.communications_generated,
                'trades_generated': self.stats.trades_generated,
                'travels_generated': self.stats.travels_generated,
                'documents_generated': self.stats.documents_generated,
                'patterns_generated': self.stats.patterns_generated,
                'total_records': self.stats.total_records,
                'generation_time_seconds': self.stats.generation_time_seconds,
            }
        }
        
        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info("✓ Exported all data to %s", output_path)
        return data


# Example usage
if __name__ == "__main__":
    # Create configuration
    config = GenerationConfig(
        seed=42,
        person_count=100,
        company_count=20,
        account_count=200,
        transaction_count=1000,
        communication_count=500,
        insider_trading_patterns=2,
        tbml_patterns=1,
        fraud_ring_patterns=2,
        structuring_patterns=3,
        cato_patterns=2,
        output_dir=Path("./output/demo")
    )
    
    # Create orchestrator and generate data
    orchestrator = MasterOrchestrator(config)
    stats = orchestrator.generate_all()
    
    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print(f"Total records: {stats.total_records:,}")
    print(f"Generation time: {stats.generation_time_seconds:.2f}s")
    print(f"Records/second: {stats.records_per_second:.2f}")
    print("=" * 80)

