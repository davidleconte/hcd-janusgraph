"""
Insider Trading Scenario Generator
===================================

Generates deterministic insider trading scenarios for educational demos
and testing. Creates realistic MNPI (Material Non-Public Information)
communications, coordinated trading patterns, and multi-hop tipping chains.

Key Features:
- Deterministic scenario generation (seed-based)
- Realistic MNPI communications with semantic content
- Multi-hop tipping chains (up to 5 hops)
- Coordinated network patterns
- Bidirectional communication sequences
- Vector-searchable content for semantic detection

Author: Banking Compliance Platform Team
Date: 2026-04-07
Sprint: 2.1 - Deterministic Data Generation
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from faker import Faker

from ..utils.data_models import Communication, Person, Trade
from ..utils.deterministic import REFERENCE_TIMESTAMP
from ..utils.helpers import generate_seeded_uuid

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class InsiderTradingScenario:
    """
    Insider trading scenario with all related entities.
    
    Attributes:
        scenario_id: Unique scenario identifier
        scenario_type: Type of scenario (multi_hop, coordinated, bidirectional)
        insider: The insider person
        tippees: List of tippee persons
        communications: MNPI communications
        trades: Trades executed after MNPI sharing
        risk_score: Expected risk score for detection
        description: Human-readable description
    """
    scenario_id: str
    scenario_type: str
    insider: Person
    tippees: List[Person]
    communications: List[Communication]
    trades: List[Trade]
    risk_score: float
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class InsiderTradingScenarioGenerator:
    """
    Generate deterministic insider trading scenarios.
    
    Scenarios:
    1. Multi-Hop Tipping Chain (5 hops)
    2. Coordinated Network (3+ participants)
    3. Bidirectional Communication (request-response)
    4. Semantic MNPI Sharing (vector-searchable)
    """
    
    # MNPI Communication Templates
    MNPI_TEMPLATES = {
        "earnings": [
            "Our Q{quarter} earnings will exceed analyst expectations by {percent}%",
            "The quarterly results are much better than forecasted - revenue up {percent}%",
            "Financial performance this quarter is exceptional - {percent}% above guidance",
            "Earnings announcement next week will surprise the market - {percent}% beat",
            "Q{quarter} results are outstanding - profit margins improved by {percent}%"
        ],
        "merger": [
            "The merger with {company} will be announced next {timeframe}",
            "Acquisition talks with {company} are in final stages - closing in {timeframe}",
            "We're buying {company} - announcement coming {timeframe}",
            "Major M&A deal with {company} - expect announcement {timeframe}",
            "Confidential: merger agreement with {company} signed, public in {timeframe}"
        ],
        "product": [
            "FDA approval for {product} expected next {timeframe}",
            "New product {product} launching {timeframe} - game changer",
            "Clinical trial results for {product} are exceptional - approval imminent",
            "{product} patent granted - major competitive advantage",
            "Regulatory approval for {product} coming {timeframe}"
        ],
        "executive": [
            "CEO resignation announcement coming {timeframe}",
            "Board approved new CEO - announcement {timeframe}",
            "Major executive changes coming - {timeframe}",
            "CFO departure will be announced {timeframe}",
            "Leadership restructuring happening {timeframe}"
        ],
        "contract": [
            "Major contract with {company} signed - ${value}M deal",
            "Government contract awarded - ${value}M over {years} years",
            "{company} partnership finalized - ${value}M revenue",
            "Exclusive supply agreement with {company} - ${value}M annually",
            "Strategic partnership with {company} - ${value}M value"
        ]
    }
    
    # Paraphrased versions for semantic similarity testing
    MNPI_PARAPHRASES = {
        "earnings": [
            "Results will surpass forecasts significantly",
            "Financial outcomes exceed projections substantially",
            "Performance metrics beat estimates considerably",
            "Quarterly figures outperform expectations notably"
        ],
        "merger": [
            "Corporate combination in progress",
            "Business consolidation underway",
            "Company integration planned",
            "Strategic union being finalized"
        ]
    }
    
    def __init__(self, seed: Optional[int] = 42):
        """
        Initialize scenario generator.
        
        Args:
            seed: Random seed for deterministic generation
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            Faker.seed(seed)
        
        self.faker = Faker()
        self._uuid_counter = 0
        
        logger.info(f"InsiderTradingScenarioGenerator initialized with seed={seed}")
    
    def generate_multi_hop_scenario(
        self,
        hops: int = 5,
        symbol: str = "ACME",
        mnpi_type: str = "earnings"
    ) -> InsiderTradingScenario:
        """
        Generate multi-hop tipping chain scenario.
        
        Creates a chain where insider tips person A, who tips person B,
        who tips person C, etc. Each person trades after receiving the tip.
        
        Args:
            hops: Number of hops in the chain (2-5)
            symbol: Stock symbol
            mnpi_type: Type of MNPI (earnings, merger, product, etc.)
            
        Returns:
            InsiderTradingScenario with multi-hop chain
        """
        logger.info(f"Generating {hops}-hop tipping chain scenario")
        
        # Generate insider (CEO)
        insider = self._generate_insider("CEO", "insider")
        
        # Generate tippee chain
        tippees = []
        for i in range(hops):
            role = f"tippee_{i+1}"
            tippee = self._generate_tippee(f"Tippee {i+1}", role)
            tippees.append(tippee)
        
        # Generate MNPI communications (chain)
        communications = []
        trades = []
        
        # Insider → Tippee 1
        comm = self._generate_mnpi_communication(
            sender=insider,
            receiver=tippees[0],
            mnpi_type=mnpi_type,
            symbol=symbol,
            hop=0
        )
        communications.append(comm)
        
        # Tippee 1 trades
        trade = self._generate_trade(
            person=tippees[0],
            symbol=symbol,
            after_communication=comm,
            value=random.randint(50000, 200000)
        )
        trades.append(trade)
        
        # Chain: Tippee i → Tippee i+1
        for i in range(len(tippees) - 1):
            comm = self._generate_mnpi_communication(
                sender=tippees[i],
                receiver=tippees[i+1],
                mnpi_type=mnpi_type,
                symbol=symbol,
                hop=i+1,
                paraphrase=True  # Use paraphrased version
            )
            communications.append(comm)
            
            # Tippee i+1 trades
            trade = self._generate_trade(
                person=tippees[i+1],
                symbol=symbol,
                after_communication=comm,
                value=random.randint(30000, 150000)
            )
            trades.append(trade)
        
        # Calculate expected risk score
        risk_score = self._calculate_expected_risk(
            scenario_type="multi_hop",
            hops=hops,
            total_value=sum(t.total_value for t in trades)
        )
        
        scenario = InsiderTradingScenario(
            scenario_id=self._generate_uuid("scenario"),
            scenario_type="multi_hop",
            insider=insider,
            tippees=tippees,
            communications=communications,
            trades=trades,
            risk_score=risk_score,
            description=f"{hops}-hop tipping chain: Insider → {' → '.join([f'Tippee {i+1}' for i in range(hops)])}",
            metadata={
                "hops": hops,
                "symbol": symbol,
                "mnpi_type": mnpi_type,
                "total_value": sum(t.total_value for t in trades),
                "detection_methods": ["multi_hop_traversal", "time_correlation"]
            }
        )
        
        logger.info(f"Generated multi-hop scenario: {scenario.scenario_id} (risk={risk_score:.3f})")
        return scenario
    
    def generate_coordinated_network_scenario(
        self,
        participants: int = 3,
        symbol: str = "TECH",
        mnpi_type: str = "merger"
    ) -> InsiderTradingScenario:
        """
        Generate coordinated network scenario.
        
        Creates a network where multiple insiders share semantically similar
        MNPI content with different tippees, who all trade in coordination.
        
        Args:
            participants: Number of insider participants (3-5)
            symbol: Stock symbol
            mnpi_type: Type of MNPI
            
        Returns:
            InsiderTradingScenario with coordinated network
        """
        logger.info(f"Generating coordinated network scenario ({participants} participants)")
        
        # Generate multiple insiders
        insiders = []
        for i in range(participants):
            role = ["CEO", "CFO", "Director", "VP", "President"][i % 5]
            insider = self._generate_insider(role, f"insider_{i+1}")
            insiders.append(insider)
        
        # Generate tippees (one per insider)
        tippees = []
        for i in range(participants):
            tippee = self._generate_tippee(f"Trader {i+1}", f"trader_{i+1}")
            tippees.append(tippee)
        
        # Generate semantically similar MNPI communications
        communications = []
        trades = []
        
        for i, (insider, tippee) in enumerate(zip(insiders, tippees)):
            # Each insider sends semantically similar message
            comm = self._generate_mnpi_communication(
                sender=insider,
                receiver=tippee,
                mnpi_type=mnpi_type,
                symbol=symbol,
                hop=i,
                paraphrase=(i > 0)  # First is original, rest are paraphrases
            )
            communications.append(comm)
            
            # Each tippee trades
            trade = self._generate_trade(
                person=tippee,
                symbol=symbol,
                after_communication=comm,
                value=random.randint(100000, 500000)
            )
            trades.append(trade)
        
        # Calculate expected risk score
        risk_score = self._calculate_expected_risk(
            scenario_type="coordinated_network",
            participants=participants,
            total_value=sum(t.total_value for t in trades)
        )
        
        scenario = InsiderTradingScenario(
            scenario_id=self._generate_uuid("scenario"),
            scenario_type="coordinated_network",
            insider=insiders[0],  # Primary insider
            tippees=tippees,
            communications=communications,
            trades=trades,
            risk_score=risk_score,
            description=f"Coordinated network: {participants} insiders sharing similar MNPI with {participants} traders",
            metadata={
                "participants": participants,
                "insiders": [i.person_id for i in insiders],
                "symbol": symbol,
                "mnpi_type": mnpi_type,
                "total_value": sum(t.total_value for t in trades),
                "detection_methods": ["vector_clustering", "semantic_similarity", "coordinated_trading"]
            }
        )
        
        logger.info(f"Generated coordinated network scenario: {scenario.scenario_id} (risk={risk_score:.3f})")
        return scenario
    
    def generate_bidirectional_scenario(
        self,
        symbol: str = "PHARMA",
        mnpi_type: str = "product"
    ) -> InsiderTradingScenario:
        """
        Generate bidirectional communication scenario.
        
        Creates request-response pattern where tippee asks for information
        and insider responds with MNPI.
        
        Args:
            symbol: Stock symbol
            mnpi_type: Type of MNPI
            
        Returns:
            InsiderTradingScenario with bidirectional communications
        """
        logger.info("Generating bidirectional communication scenario")
        
        # Generate insider and tippee
        insider = self._generate_insider("CFO", "insider")
        tippee = self._generate_tippee("Trader", "trader")
        
        # Generate request-response communications
        communications = []
        
        # Request from tippee
        request = self._generate_request_communication(
            sender=tippee,
            receiver=insider,
            mnpi_type=mnpi_type,
            symbol=symbol
        )
        communications.append(request)
        
        # Response from insider (with MNPI)
        response = self._generate_mnpi_communication(
            sender=insider,
            receiver=tippee,
            mnpi_type=mnpi_type,
            symbol=symbol,
            hop=0,
            is_response=True
        )
        communications.append(response)
        
        # Tippee trades after receiving MNPI
        trade = self._generate_trade(
            person=tippee,
            symbol=symbol,
            after_communication=response,
            value=random.randint(150000, 300000)
        )
        
        # Calculate expected risk score
        risk_score = self._calculate_expected_risk(
            scenario_type="bidirectional",
            total_value=trade.total_value
        )
        
        scenario = InsiderTradingScenario(
            scenario_id=self._generate_uuid("scenario"),
            scenario_type="bidirectional",
            insider=insider,
            tippees=[tippee],
            communications=communications,
            trades=[trade],
            risk_score=risk_score,
            description="Bidirectional communication: Tippee requests information, insider responds with MNPI",
            metadata={
                "symbol": symbol,
                "mnpi_type": mnpi_type,
                "total_value": trade.total_value,
                "detection_methods": ["bidirectional_analysis", "request_response_pattern"]
            }
        )
        
        logger.info(f"Generated bidirectional scenario: {scenario.scenario_id} (risk={risk_score:.3f})")
        return scenario
    
    def _generate_insider(self, job_title: str, role: str) -> Person:
        """Generate insider person with executive role."""
        person_id = self._generate_uuid(role)
        
        return Person(
            person_id=person_id,
            first_name=self.faker.first_name(),
            last_name=self.faker.last_name(),
            date_of_birth=self.faker.date_of_birth(minimum_age=35, maximum_age=65),
            nationality=self.faker.country_code(),
            job_title=job_title,
            employer="ACME Corporation",
            is_pep=True,  # Politically Exposed Person
            risk_level="HIGH",
            created_at=REFERENCE_TIMESTAMP
        )
    
    def _generate_tippee(self, name: str, role: str) -> Person:
        """Generate tippee person."""
        person_id = self._generate_uuid(role)
        
        return Person(
            person_id=person_id,
            first_name=name.split()[0] if ' ' in name else name,
            last_name=name.split()[1] if ' ' in name else "Trader",
            date_of_birth=self.faker.date_of_birth(minimum_age=25, maximum_age=55),
            nationality=self.faker.country_code(),
            job_title="Trader",
            employer="Investment Firm",
            is_pep=False,
            risk_level="MEDIUM",
            created_at=REFERENCE_TIMESTAMP
        )
    
    def _generate_mnpi_communication(
        self,
        sender: Person,
        receiver: Person,
        mnpi_type: str,
        symbol: str,
        hop: int,
        paraphrase: bool = False,
        is_response: bool = False
    ) -> Communication:
        """Generate MNPI communication."""
        comm_id = self._generate_uuid(f"comm_{hop}")
        
        # Select template
        if paraphrase and mnpi_type in self.MNPI_PARAPHRASES:
            templates = self.MNPI_PARAPHRASES[mnpi_type]
        else:
            templates = self.MNPI_TEMPLATES.get(mnpi_type, self.MNPI_TEMPLATES["earnings"])
        
        template = random.choice(templates)
        
        # Fill template
        content = template.format(
            quarter=random.choice(["1", "2", "3", "4"]),
            percent=random.randint(15, 35),
            company=random.choice(["TechCorp", "DataSystems", "CloudServices"]),
            timeframe=random.choice(["week", "month", "two weeks"]),
            product=random.choice(["DrugX", "DeviceY", "TherapyZ"]),
            value=random.randint(50, 500),
            years=random.randint(3, 7)
        )
        
        if is_response:
            content = f"Re: Your question - {content}"
        
        # Calculate timestamp (hop * 2 hours after reference)
        timestamp = REFERENCE_TIMESTAMP + timedelta(hours=hop * 2)
        
        return Communication(
            communication_id=comm_id,
            sender_id=sender.person_id,
            receiver_id=receiver.person_id,
            content=content,
            channel="email",
            timestamp=timestamp,
            contains_suspicious_keywords=True,
            mnpi_similarity=random.uniform(0.85, 0.95),  # High MNPI content
            created_at=REFERENCE_TIMESTAMP
        )
    
    def _generate_request_communication(
        self,
        sender: Person,
        receiver: Person,
        mnpi_type: str,
        symbol: str
    ) -> Communication:
        """Generate request communication (no MNPI)."""
        comm_id = self._generate_uuid("request")
        
        requests = [
            f"How are things looking for {symbol} this quarter?",
            f"Any updates on the {symbol} situation?",
            f"What's the latest on {symbol}?",
            f"Can you share any insights on {symbol}?",
            f"Do you have any information about {symbol}?"
        ]
        
        content = random.choice(requests)
        timestamp = REFERENCE_TIMESTAMP
        
        return Communication(
            communication_id=comm_id,
            sender_id=sender.person_id,
            receiver_id=receiver.person_id,
            content=content,
            channel="email",
            timestamp=timestamp,
            contains_suspicious_keywords=False,
            mnpi_similarity=0.3,  # Low MNPI content (just asking)
            created_at=REFERENCE_TIMESTAMP
        )
    
    def _generate_trade(
        self,
        person: Person,
        symbol: str,
        after_communication: Communication,
        value: int
    ) -> Trade:
        """Generate trade after receiving MNPI."""
        trade_id = self._generate_uuid("trade")
        
        # Trade 1-24 hours after communication
        trade_time = after_communication.timestamp + timedelta(hours=random.randint(1, 24))
        
        quantity = value // random.randint(50, 150)  # Share price
        
        return Trade(
            trade_id=trade_id,
            person_id=person.person_id,
            symbol=symbol,
            trade_type="BUY",
            quantity=quantity,
            price=value / quantity,
            total_value=value,
            timestamp=trade_time,
            created_at=REFERENCE_TIMESTAMP
        )
    
    def _calculate_expected_risk(
        self,
        scenario_type: str,
        **kwargs
    ) -> float:
        """Calculate expected risk score for scenario."""
        if scenario_type == "multi_hop":
            hops = kwargs.get('hops', 3)
            total_value = kwargs.get('total_value', 0)
            
            hop_score = min(hops / 5.0, 1.0)
            value_score = min(total_value / 1_000_000, 1.0)
            
            return round(hop_score * 0.6 + value_score * 0.4, 3)
        
        elif scenario_type == "coordinated_network":
            participants = kwargs.get('participants', 3)
            total_value = kwargs.get('total_value', 0)
            
            participant_score = min(participants / 5.0, 1.0)
            value_score = min(total_value / 2_000_000, 1.0)
            
            return round(participant_score * 0.5 + value_score * 0.5, 3)
        
        elif scenario_type == "bidirectional":
            total_value = kwargs.get('total_value', 0)
            value_score = min(total_value / 500_000, 1.0)
            
            return round(0.7 + value_score * 0.3, 3)
        
        return 0.5
    
    def _generate_uuid(self, prefix: str) -> str:
        """Generate deterministic UUID."""
        uuid = generate_seeded_uuid(self.seed, self._uuid_counter, prefix)
        self._uuid_counter += 1
        return uuid
    
    def generate_all_scenarios(self) -> List[InsiderTradingScenario]:
        """
        Generate all scenario types for comprehensive demo.
        
        Returns:
            List of all scenarios
        """
        logger.info("Generating all insider trading scenarios")
        
        scenarios = []
        
        # Multi-hop scenarios (3, 4, 5 hops)
        for hops in [3, 4, 5]:
            scenario = self.generate_multi_hop_scenario(hops=hops)
            scenarios.append(scenario)
        
        # Coordinated network scenarios (3, 4, 5 participants)
        for participants in [3, 4, 5]:
            scenario = self.generate_coordinated_network_scenario(participants=participants)
            scenarios.append(scenario)
        
        # Bidirectional scenario
        scenario = self.generate_bidirectional_scenario()
        scenarios.append(scenario)
        
        logger.info(f"Generated {len(scenarios)} scenarios")
        return scenarios


if __name__ == "__main__":
    # Example usage
    generator = InsiderTradingScenarioGenerator(seed=42)
    
    # Generate all scenarios
    scenarios = generator.generate_all_scenarios()
    
    print(f"\nGenerated {len(scenarios)} insider trading scenarios:")
    print("=" * 80)
    
    for scenario in scenarios:
        print(f"\nScenario: {scenario.scenario_id}")
        print(f"Type: {scenario.scenario_type}")
        print(f"Description: {scenario.description}")
        print(f"Risk Score: {scenario.risk_score:.3f}")
        print(f"Communications: {len(scenario.communications)}")
        print(f"Trades: {len(scenario.trades)}")
        print(f"Total Value: ${sum(t.total_value for t in scenario.trades):,.2f}")
        print(f"Detection Methods: {', '.join(scenario.metadata['detection_methods'])}")

# Made with Bob
