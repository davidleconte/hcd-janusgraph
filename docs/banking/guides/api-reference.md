# Synthetic Data Generators - API Reference

Complete API documentation for all data generator components.

**Version**: 1.0.0
**Last Updated**: 2026-01-28

---

## Table of Contents

1. [Core Generators](#core-generators)
2. [Event Generators](#event-generators)
3. [Pattern Generators](#pattern-generators)
4. [Orchestration](#orchestration)
5. [Data Models](#data-models)
6. [Utilities](#utilities)

---

## Core Generators

### PersonGenerator

Generates synthetic person entities with realistic attributes.

#### Class Definition

```python
from banking.data_generators.core.person_generator import PersonGenerator

class PersonGenerator(BaseGenerator):
    """Generate synthetic person entities"""
```

#### Constructor

```python
PersonGenerator(seed: Optional[int] = None)
```

**Parameters**:

- `seed` (int, optional): Random seed for reproducibility

**Example**:

```python
generator = PersonGenerator(seed=42)
```

#### Methods

##### generate()

```python
def generate() -> Person
```

Generate a single person entity.

**Returns**: `Person` - Generated person object

**Example**:

```python
person = generator.generate()
print(f"Generated: {person.first_name} {person.last_name}")
print(f"Age: {person.age}, Risk Level: {person.risk_level}")
```

**Person Attributes**:

- `person_id` (str): Unique identifier (format: PER-{12-CHAR-ID})
- `first_name` (str): First name
- `last_name` (str): Last name
- `date_of_birth` (date): Date of birth
- `age` (int): Calculated age
- `nationality` (str): ISO country code
- `gender` (str): Gender
- `email_addresses` (List[Email]): Email addresses
- `phone_numbers` (List[Phone]): Phone numbers
- `addresses` (List[Address]): Physical addresses
- `employment` (Employment): Employment information
- `risk_level` (str): Risk level (low, medium, high, critical)
- `risk_score` (float): Risk score (0.0-1.0)
- `is_pep` (bool): Politically Exposed Person flag
- `created_at` (datetime): Creation timestamp

---

### CompanyGenerator

Generates synthetic company entities.

#### Class Definition

```python
from banking.data_generators.core.company_generator import CompanyGenerator

class CompanyGenerator(BaseGenerator):
    """Generate synthetic company entities"""
```

#### Constructor

```python
CompanyGenerator(seed: Optional[int] = None)
```

#### Methods

##### generate()

```python
def generate() -> Company
```

Generate a single company entity.

**Returns**: `Company` - Generated company object

**Example**:

```python
generator = CompanyGenerator(seed=42)
company = generator.generate()
print(f"Company: {company.name}")
print(f"Industry: {company.industry}, Revenue: ${company.annual_revenue:,.2f}")
```

**Company Attributes**:

- `company_id` (str): Unique identifier (format: COM-{12-CHAR-ID})
- `name` (str): Company name
- `legal_name` (str): Legal entity name
- `industry` (str): Industry classification
- `incorporation_date` (date): Date of incorporation
- `jurisdiction` (str): Jurisdiction of incorporation
- `tax_id` (str): Tax identification number
- `annual_revenue` (float): Annual revenue
- `employee_count` (int): Number of employees
- `addresses` (List[Address]): Business addresses
- `risk_level` (str): Risk level
- `risk_score` (float): Risk score (0.0-1.0)
- `is_public` (bool): Publicly traded flag
- `created_at` (datetime): Creation timestamp

---

### AccountGenerator

Generates synthetic bank account entities.

#### Class Definition

```python
from banking.data_generators.core.account_generator import AccountGenerator

class AccountGenerator(BaseGenerator):
    """Generate synthetic account entities"""
```

#### Constructor

```python
AccountGenerator(seed: Optional[int] = None)
```

#### Methods

##### generate()

```python
def generate(owner: Union[Person, Company]) -> Account
```

Generate a single account entity.

**Parameters**:

- `owner` (Person | Company): Account owner (person or company)

**Returns**: `Account` - Generated account object

**Example**:

```python
person_gen = PersonGenerator(seed=42)
account_gen = AccountGenerator(seed=42)

person = person_gen.generate()
account = account_gen.generate(owner=person)

print(f"Account: {account.account_number}")
print(f"Type: {account.account_type}, Balance: ${account.balance:,.2f}")
```

**Account Attributes**:

- `account_id` (str): Unique identifier (format: ACC-{12-CHAR-ID})
- `account_number` (str): Account number
- `account_type` (str): Account type (checking, savings, investment, etc.)
- `currency` (str): Currency code
- `balance` (float): Current balance
- `owner_person_id` (str, optional): Owner person ID
- `owner_company_id` (str, optional): Owner company ID
- `opened_date` (date): Account opening date
- `status` (str): Account status (active, closed, frozen)
- `risk_level` (str): Risk level
- `created_at` (datetime): Creation timestamp

---

## Event Generators

### TransactionGenerator

Generates synthetic financial transactions.

#### Class Definition

```python
from banking.data_generators.events.transaction_generator import TransactionGenerator

class TransactionGenerator(BaseGenerator):
    """Generate synthetic transaction events"""
```

#### Constructor

```python
TransactionGenerator(seed: Optional[int] = None)
```

#### Methods

##### generate()

```python
def generate(
    from_account: Account,
    to_account: Account,
    timestamp: Optional[datetime] = None
) -> Transaction
```

Generate a single transaction.

**Parameters**:

- `from_account` (Account): Source account
- `to_account` (Account): Destination account
- `timestamp` (datetime, optional): Transaction timestamp

**Returns**: `Transaction` - Generated transaction object

**Example**:

```python
txn_gen = TransactionGenerator(seed=42)
transaction = txn_gen.generate(
    from_account=account1,
    to_account=account2
)

print(f"Transaction: {transaction.transaction_id}")
print(f"Amount: ${transaction.amount:,.2f} {transaction.currency}")
print(f"Type: {transaction.transaction_type}")
```

**Transaction Attributes**:

- `transaction_id` (str): Unique identifier (format: TXN-{16-CHAR-ID})
- `from_account_id` (str): Source account ID
- `to_account_id` (str): Destination account ID
- `amount` (float): Transaction amount
- `currency` (str): Currency code
- `timestamp` (datetime): Transaction timestamp
- `transaction_type` (str): Type (wire_transfer, ach, check, etc.)
- `description` (str): Transaction description
- `is_suspicious` (bool): Suspicious flag
- `risk_score` (float): Risk score (0.0-1.0)
- `metadata` (dict): Additional metadata

---

### CommunicationGenerator

Generates synthetic communication events.

#### Class Definition

```python
from banking.data_generators.events.communication_generator import CommunicationGenerator
```

#### Methods

##### generate()

```python
def generate(
    from_person: Person,
    to_person: Person,
    timestamp: Optional[datetime] = None
) -> Communication
```

Generate a communication event.

**Communication Attributes**:

- `communication_id` (str): Unique identifier
- `from_person_id` (str): Sender person ID
- `to_person_id` (str): Recipient person ID
- `communication_type` (str): Type (email, phone, meeting, etc.)
- `timestamp` (datetime): Communication timestamp
- `subject` (str): Subject/topic
- `is_suspicious` (bool): Suspicious flag

---

### TradeGenerator

Generates synthetic securities trade events.

#### Class Definition

```python
from banking.data_generators.events.trade_generator import TradeGenerator
```

#### Methods

##### generate()

```python
def generate(
    account: Account,
    timestamp: Optional[datetime] = None
) -> Trade
```

Generate a securities trade.

**Trade Attributes**:

- `trade_id` (str): Unique identifier
- `account_id` (str): Trading account ID
- `security_symbol` (str): Security ticker symbol
- `trade_type` (str): Type (buy, sell)
- `quantity` (int): Number of shares
- `price` (float): Price per share
- `timestamp` (datetime): Trade timestamp
- `is_suspicious` (bool): Suspicious flag

---

### TravelGenerator

Generates synthetic travel events.

#### Class Definition

```python
from banking.data_generators.events.travel_generator import TravelGenerator
```

#### Methods

##### generate()

```python
def generate(
    person: Person,
    timestamp: Optional[datetime] = None
) -> Travel
```

Generate a travel event.

**Travel Attributes**:

- `travel_id` (str): Unique identifier
- `person_id` (str): Traveler person ID
- `origin_country` (str): Origin country code
- `destination_country` (str): Destination country code
- `departure_date` (date): Departure date
- `return_date` (date): Return date
- `purpose` (str): Travel purpose
- `is_suspicious` (bool): Suspicious flag

---

### DocumentGenerator

Generates synthetic document events.

#### Class Definition

```python
from banking.data_generators.events.document_generator import DocumentGenerator
```

#### Methods

##### generate()

```python
def generate(
    owner: Union[Person, Company],
    timestamp: Optional[datetime] = None
) -> Document
```

Generate a document event.

**Document Attributes**:

- `document_id` (str): Unique identifier
- `owner_person_id` (str, optional): Owner person ID
- `owner_company_id` (str, optional): Owner company ID
- `document_type` (str): Type (passport, license, contract, etc.)
- `issue_date` (date): Issue date
- `expiry_date` (date): Expiry date
- `issuing_authority` (str): Issuing authority
- `is_suspicious` (bool): Suspicious flag

---

## Pattern Generators

### InsiderTradingPatternGenerator

Generates insider trading patterns.

#### Class Definition

```python
from banking.data_generators.patterns.insider_trading_pattern import InsiderTradingPatternGenerator
```

#### Methods

##### inject_pattern()

```python
def inject_pattern(
    persons: List[Person],
    companies: List[Company],
    accounts: List[Account],
    trades: List[Trade],
    communications: List[Communication]
) -> Dict[str, Any]
```

Inject insider trading pattern into existing data.

**Parameters**:

- `persons`: List of person entities
- `companies`: List of company entities
- `accounts`: List of account entities
- `trades`: List of trade events
- `communications`: List of communication events

**Returns**: Dictionary with pattern metadata

**Example**:

```python
pattern_gen = InsiderTradingPatternGenerator(seed=42)
pattern_info = pattern_gen.inject_pattern(
    persons=persons,
    companies=companies,
    accounts=accounts,
    trades=trades,
    communications=communications
)

print(f"Pattern ID: {pattern_info['pattern_id']}")
print(f"Insider: {pattern_info['insider_id']}")
print(f"Trades: {len(pattern_info['trade_ids'])}")
```

---

### TBMLPatternGenerator

Generates Trade-Based Money Laundering patterns.

#### Class Definition

```python
from banking.data_generators.patterns.tbml_pattern import TBMLPatternGenerator
```

#### Methods

##### inject_pattern()

```python
def inject_pattern(
    companies: List[Company],
    accounts: List[Account],
    transactions: List[Transaction],
    documents: List[Document]
) -> Dict[str, Any]
```

Inject TBML pattern into existing data.

---

### FraudRingPatternGenerator

Generates fraud ring patterns.

#### Class Definition

```python
from banking.data_generators.patterns.fraud_ring_pattern import FraudRingPatternGenerator
```

#### Methods

##### inject_pattern()

```python
def inject_pattern(
    persons: List[Person],
    accounts: List[Account],
    transactions: List[Transaction]
) -> Dict[str, Any]
```

Inject fraud ring pattern into existing data.

---

### StructuringPatternGenerator

Generates structuring (smurfing) patterns.

#### Class Definition

```python
from banking.data_generators.patterns.structuring_pattern import StructuringPatternGenerator
```

#### Methods

##### inject_pattern()

```python
def inject_pattern(
    persons: List[Person],
    accounts: List[Account],
    transactions: List[Transaction]
) -> Dict[str, Any]
```

Inject structuring pattern into existing data.

---

### CATOPatternGenerator

Generates Coordinated Account Takeover patterns.

#### Class Definition

```python
from banking.data_generators.patterns.cato_pattern import CATOPatternGenerator
```

#### Methods

##### inject_pattern()

```python
def inject_pattern(
    persons: List[Person],
    accounts: List[Account],
    transactions: List[Transaction]
) -> Dict[str, Any]
```

Inject CATO pattern into existing data.

---

## Orchestration

### MasterOrchestrator

Coordinates all generators and pattern injection.

#### Class Definition

```python
from banking.data_generators.orchestration import MasterOrchestrator, GenerationConfig

class MasterOrchestrator:
    """Master orchestrator for data generation"""
```

#### Constructor

```python
MasterOrchestrator(config: GenerationConfig)
```

**Parameters**:

- `config` (GenerationConfig): Generation configuration

**Example**:

```python
from pathlib import Path

config = GenerationConfig(
    seed=42,
    person_count=1000,
    company_count=500,
    account_count=2000,
    transaction_count=10000,
    insider_trading_patterns=2,
    fraud_ring_patterns=1,
    output_dir=Path("./output")
)

orchestrator = MasterOrchestrator(config)
```

#### Methods

##### generate_all()

```python
def generate_all() -> GenerationStats
```

Generate all entities, events, and patterns.

**Returns**: `GenerationStats` - Generation statistics

**Example**:

```python
stats = orchestrator.generate_all()

print(f"Persons: {stats.persons_generated}")
print(f"Companies: {stats.companies_generated}")
print(f"Accounts: {stats.accounts_generated}")
print(f"Transactions: {stats.transactions_generated}")
print(f"Duration: {stats.duration_seconds:.2f}s")
```

##### export_to_json()

```python
def export_to_json(output_file: Path) -> None
```

Export generated data to JSON file.

**Parameters**:

- `output_file` (Path): Output file path

**Example**:

```python
orchestrator.export_to_json(Path("./output/data.json"))
```

---

### GenerationConfig

Configuration for data generation.

#### Class Definition

```python
@dataclass
class GenerationConfig:
    """Configuration for data generation"""
```

#### Attributes

```python
seed: int = 42
person_count: int = 100
company_count: int = 50
account_count: int = 200
transaction_count: int = 1000
communication_count: int = 500
trade_count: int = 300
travel_count: int = 100
document_count: int = 200
insider_trading_patterns: int = 0
tbml_patterns: int = 0
fraud_ring_patterns: int = 0
structuring_patterns: int = 0
cato_patterns: int = 0
output_dir: Path = Path("./output")
```

**Example**:

```python
config = GenerationConfig(
    seed=42,
    person_count=1000,
    company_count=500,
    account_count=2000,
    transaction_count=10000,
    insider_trading_patterns=2,
    tbml_patterns=1,
    fraud_ring_patterns=1,
    structuring_patterns=2,
    cato_patterns=1,
    output_dir=Path("./data")
)
```

---

### GenerationStats

Statistics from data generation.

#### Class Definition

```python
@dataclass
class GenerationStats:
    """Statistics from data generation"""
```

#### Attributes

```python
persons_generated: int
companies_generated: int
accounts_generated: int
transactions_generated: int
communications_generated: int
trades_generated: int
travels_generated: int
documents_generated: int
patterns_injected: int
duration_seconds: float
errors: List[str]
```

---

## Data Models

### Person

```python
@dataclass
class Person:
    person_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    age: int
    nationality: str
    gender: str
    email_addresses: List[Email]
    phone_numbers: List[Phone]
    addresses: List[Address]
    employment: Optional[Employment]
    risk_level: str
    risk_score: float
    is_pep: bool
    created_at: datetime
```

### Company

```python
@dataclass
class Company:
    company_id: str
    name: str
    legal_name: str
    industry: str
    incorporation_date: date
    jurisdiction: str
    tax_id: str
    annual_revenue: float
    employee_count: int
    addresses: List[Address]
    risk_level: str
    risk_score: float
    is_public: bool
    created_at: datetime
```

### Account

```python
@dataclass
class Account:
    account_id: str
    account_number: str
    account_type: str
    currency: str
    balance: float
    owner_person_id: Optional[str]
    owner_company_id: Optional[str]
    opened_date: date
    status: str
    risk_level: str
    created_at: datetime
```

### Transaction

```python
@dataclass
class Transaction:
    transaction_id: str
    from_account_id: str
    to_account_id: str
    amount: float
    currency: str
    timestamp: datetime
    transaction_type: str
    description: str
    is_suspicious: bool
    risk_score: float
    metadata: Dict[str, Any]
```

---

## Utilities

### Helpers

```python
from banking.data_generators.utils.helpers import (
    generate_id,
    calculate_age,
    generate_risk_score,
    format_currency
)
```

#### generate_id()

```python
def generate_id(prefix: str, length: int = 12) -> str
```

Generate unique identifier with prefix.

**Example**:

```python
person_id = generate_id("PER", 12)  # "PER-ABC123DEF456"
```

#### calculate_age()

```python
def calculate_age(birth_date: date) -> int
```

Calculate age from birth date.

#### generate_risk_score()

```python
def generate_risk_score() -> float
```

Generate risk score between 0.0 and 1.0.

---

### Constants

```python
from banking.data_generators.utils.constants import (
    RISK_LEVELS,
    ACCOUNT_TYPES,
    TRANSACTION_TYPES,
    CURRENCIES
)
```

#### Available Constants

- `RISK_LEVELS`: ['low', 'medium', 'high', 'critical']
- `ACCOUNT_TYPES`: ['checking', 'savings', 'investment', 'business']
- `TRANSACTION_TYPES`: ['wire_transfer', 'ach', 'check', 'cash_deposit', ...]
- `CURRENCIES`: ['USD', 'EUR', 'GBP', 'JPY', 'CHF', ...]

---

## Error Handling

All generators may raise the following exceptions:

### GenerationError

```python
class GenerationError(Exception):
    """Base exception for generation errors"""
```

Raised when data generation fails.

**Example**:

```python
try:
    person = generator.generate()
except GenerationError as e:
    print(f"Generation failed: {e}")
```

### ValidationError

```python
class ValidationError(Exception):
    """Exception for validation errors"""
```

Raised when data validation fails.

---

## Best Practices

### 1. Use Seeds for Reproducibility

```python
# Always use seeds for reproducible results
generator = PersonGenerator(seed=42)
```

### 2. Reuse Generator Instances

```python
# Reuse generators for better performance
person_gen = PersonGenerator(seed=42)
persons = [person_gen.generate() for _ in range(1000)]
```

### 3. Use Orchestrator for Complex Scenarios

```python
# Use orchestrator for coordinated generation
config = GenerationConfig(seed=42, person_count=1000)
orchestrator = MasterOrchestrator(config)
stats = orchestrator.generate_all()
```

### 4. Handle Errors Gracefully

```python
try:
    stats = orchestrator.generate_all()
except GenerationError as e:
    logger.error(f"Generation failed: {e}")
    # Handle error appropriately
```

### 5. Validate Generated Data

```python
# Always validate critical data
assert person.age >= 18
assert account.balance >= 0
assert transaction.amount > 0
```

---

## Version History

- **1.0.0** (2026-01-28): Initial release
  - All 14 generators implemented
  - Master orchestrator
  - 5 pattern generators
  - Complete test suite

---

## Support

For issues, questions, or contributions:

- Documentation: `docs/banking/`
- Examples: `banking/data_generators/examples/`
- Tests: `banking/data_generators/tests/`
- Issues: Contact development team

---

**Last Updated**: 2026-01-28
**Version**: 1.0.0
