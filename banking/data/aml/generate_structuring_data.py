#!/usr/bin/env python3
"""
AML Structuring/Smurfing Pattern - Synthetic Data Generator

Generates realistic banking data with embedded structuring (smurfing) patterns
for anti-money laundering detection.

Pattern: Multiple small deposits (<$10,000 reporting threshold) from
coordinated accounts converging to a single beneficiary account.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team
Contact: team@example.com
Date: 2026-02-06
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List

from faker import Faker

# Initialize Faker for realistic data
fake = Faker()
Faker.seed(42)  # Reproducible results
random.seed(42)

# Constants
STRUCTURING_THRESHOLD = 10000  # $10,000 reporting threshold
STRUCTURING_BUFFER = 1000  # Stay this much below threshold


class AMLDataGenerator:
    """Generate synthetic AML data with structuring patterns"""

    def __init__(
        self,
        num_normal_customers=50,
        num_mule_accounts=10,
        num_beneficiaries=2,
        time_window_hours=24,
    ):
        """
        Initialize generator

        Args:
            num_normal_customers: Number of normal customers (noise)
            num_mule_accounts: Number of mule accounts per structuring ring
            num_beneficiaries: Number of beneficiary accounts (money launderers)
            time_window_hours: Time window for coordinated transactions
        """
        self.num_normal_customers = num_normal_customers
        self.num_mule_accounts = num_mule_accounts
        self.num_beneficiaries = num_beneficiaries
        self.time_window_hours = time_window_hours

        # Data storage
        self.persons = []
        self.accounts = []
        self.transactions = []
        self.addresses = []
        self.phones = []

        # ID counters
        self.person_counter = 1
        self.account_counter = 1
        self.transaction_counter = 1
        self.address_counter = 1
        self.phone_counter = 1

    def generate_person_id(self) -> str:
        """Generate unique person ID"""
        pid = f"P{self.person_counter:06d}"
        self.person_counter += 1
        return pid

    def generate_account_id(self) -> str:
        """Generate unique account ID"""
        aid = f"ACC{self.account_counter:08d}"
        self.account_counter += 1
        return aid

    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        tid = f"TXN{self.transaction_counter:010d}"
        self.transaction_counter += 1
        return tid

    def generate_ssn(self) -> str:
        """Generate fake SSN"""
        return f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"

    def create_person(self, is_mule=False, is_beneficiary=False) -> Dict:
        """Create a person entity"""
        person = {
            "person_id": self.generate_person_id(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "ssn": self.generate_ssn(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            "risk_score": 0.8 if (is_mule or is_beneficiary) else random.uniform(0.1, 0.3),
            "flagged": is_beneficiary,
            "flag_reason": "structuring_beneficiary" if is_beneficiary else None,
        }
        return person

    def create_address(self, shared=False) -> Dict:
        """Create an address entity"""
        address_id = f"ADDR{self.address_counter:06d}"
        self.address_counter += 1

        address = {
            "address_id": address_id,
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
        }
        return address

    def create_phone(self) -> Dict:
        """Create a phone entity"""
        phone_id = f"PHONE{self.phone_counter:06d}"
        self.phone_counter += 1

        phone = {"phone_id": phone_id, "phone_number": fake.phone_number()}
        return phone

    def create_account(self, person_id: str, account_type="checking", is_beneficiary=False) -> Dict:
        """Create an account entity"""
        account = {
            "account_id": self.generate_account_id(),
            "account_type": account_type,
            "account_status": "active",
            "balance": (
                random.uniform(50000, 500000) if is_beneficiary else random.uniform(1000, 50000)
            ),
            "open_date": fake.date_between(start_date="-5y", end_date="-1y").isoformat(),
            "owner_person_id": person_id,
        }
        return account

    def create_transaction(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: float,
        timestamp: datetime,
        is_structuring=False,
    ) -> Dict:
        """Create a transaction entity"""
        transaction = {
            "transaction_id": self.generate_transaction_id(),
            "amount": round(amount, 2),
            "transaction_type": (
                "deposit"
                if is_structuring
                else random.choice(["deposit", "withdrawal", "transfer"])
            ),
            "timestamp": int(timestamp.timestamp()),
            "date": timestamp.date().isoformat(),
            "description": self.generate_transaction_description(amount, is_structuring),
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "suspicious_pattern": "structuring" if is_structuring else None,
        }
        return transaction

    def generate_transaction_description(self, amount: float, is_structuring=False) -> str:
        """Generate realistic transaction description"""
        if is_structuring:
            # Structuring transactions try to look normal
            templates = [
                "Cash deposit - business income",
                "Deposit - consulting payment",
                "Cash deposit - service fees",
                "Deposit - miscellaneous income",
            ]
        else:
            templates = [
                "ACH transfer",
                "Wire transfer",
                "Check deposit",
                "ATM withdrawal",
                "Debit card purchase",
                "Online payment",
            ]
        return random.choice(templates)

    def generate_structuring_pattern(
        self, beneficiary_account_id: str, mule_accounts: List[Dict], start_time: datetime
    ) -> List[Dict]:
        """
        Generate structuring pattern: multiple small deposits to beneficiary

        Pattern characteristics:
        - Multiple accounts deposit to same beneficiary
        - Amounts just below $10,000 threshold
        - Transactions clustered in time (coordinated)
        - Slight variations to avoid exact patterns
        """
        transactions = []

        # Each mule account makes 2-5 deposits within time window
        for mule_account in mule_accounts:
            num_deposits = random.randint(2, 5)

            for i in range(num_deposits):
                # Amount just below threshold, with variation
                base_amount = STRUCTURING_THRESHOLD - STRUCTURING_BUFFER
                amount = base_amount + random.uniform(-500, 500)

                # Time within window, slightly staggered
                time_offset = random.uniform(0, self.time_window_hours * 3600)
                transaction_time = start_time + timedelta(seconds=time_offset)

                transaction = self.create_transaction(
                    from_account_id=mule_account["account_id"],
                    to_account_id=beneficiary_account_id,
                    amount=amount,
                    timestamp=transaction_time,
                    is_structuring=True,
                )
                transactions.append(transaction)

        return transactions

    def generate_normal_transactions(
        self, accounts: List[Dict], num_transactions: int, start_date: datetime, end_date: datetime
    ) -> List[Dict]:
        """Generate normal transactions (noise) for realism"""
        transactions = []

        for _ in range(num_transactions):
            # Random account pair
            from_account = random.choice(accounts)
            to_account = random.choice([a for a in accounts if a != from_account])

            # Random amount (wider range than structuring)
            amount = random.choice(
                [
                    random.uniform(10, 500),  # Small transactions
                    random.uniform(500, 5000),  # Medium transactions
                    random.uniform(5000, 50000),  # Large legitimate transactions
                ]
            )

            # Random timestamp
            time_range = (end_date - start_date).total_seconds()
            random_offset = random.uniform(0, time_range)
            transaction_time = start_date + timedelta(seconds=random_offset)

            transaction = self.create_transaction(
                from_account_id=from_account["account_id"],
                to_account_id=to_account["account_id"],
                amount=amount,
                timestamp=transaction_time,
                is_structuring=False,
            )
            transactions.append(transaction)

        return transactions

    def generate_all_data(self) -> Dict:
        """Generate complete synthetic dataset with structuring patterns"""
        print("🔧 Generating AML synthetic data...")

        # Time range for all transactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # 90 days of data

        # Create shared addresses/phones for mule accounts (coordination signal)
        shared_address = self.create_address(shared=True)
        shared_phone = self.create_phone()
        self.addresses.append(shared_address)
        self.phones.append(shared_phone)

        # Generate beneficiaries (launderers)
        print(f"  Creating {self.num_beneficiaries} beneficiaries...")
        beneficiary_persons = []
        beneficiary_accounts = []

        for _ in range(self.num_beneficiaries):
            person = self.create_person(is_beneficiary=True)
            self.persons.append(person)
            beneficiary_persons.append(person)

            # Each beneficiary has 1-2 accounts
            for _ in range(random.randint(1, 2)):
                account = self.create_account(person["person_id"], is_beneficiary=True)
                self.accounts.append(account)
                beneficiary_accounts.append(account)

                # Beneficiary has own address/phone
                address = self.create_address()
                phone = self.create_phone()
                self.addresses.append(address)
                self.phones.append(phone)

        # Generate mule accounts (for each beneficiary)
        print(f"  Creating {self.num_mule_accounts} mule accounts per beneficiary...")
        all_mule_accounts = []

        for beneficiary in beneficiary_accounts:
            mule_accounts_for_beneficiary = []

            for _ in range(self.num_mule_accounts):
                person = self.create_person(is_mule=True)
                self.persons.append(person)

                account = self.create_account(person["person_id"])
                self.accounts.append(account)
                mule_accounts_for_beneficiary.append(account)
                all_mule_accounts.append(account)

                # Some mules share address/phone (coordination signal)
                if random.random() < 0.3:  # 30% share address
                    # Use shared address (already created)
                    pass
                else:
                    # Create unique address
                    address = self.create_address()
                    self.addresses.append(address)

                # Some share phone
                if random.random() < 0.4:  # 40% share phone
                    # Use shared phone
                    pass
                else:
                    phone = self.create_phone()
                    self.phones.append(phone)

            # Generate structuring pattern for this beneficiary
            print(f"    Generating structuring pattern for {beneficiary['account_id']}...")
            structuring_start = end_date - timedelta(days=random.randint(1, 30))
            structuring_txns = self.generate_structuring_pattern(
                beneficiary_account_id=beneficiary["account_id"],
                mule_accounts=mule_accounts_for_beneficiary,
                start_time=structuring_start,
            )
            self.transactions.extend(structuring_txns)

        # Generate normal customers (noise)
        print(f"  Creating {self.num_normal_customers} normal customers...")
        normal_accounts = []

        for _ in range(self.num_normal_customers):
            person = self.create_person()
            self.persons.append(person)

            # Each person has 1-3 accounts
            for _ in range(random.randint(1, 3)):
                account = self.create_account(person["person_id"])
                self.accounts.append(account)
                normal_accounts.append(account)

                address = self.create_address()
                phone = self.create_phone()
                self.addresses.append(address)
                self.phones.append(phone)

        # Generate normal transactions (noise)
        print("  Generating normal transactions...")
        all_accounts = beneficiary_accounts + all_mule_accounts + normal_accounts
        num_normal_txns = len(self.transactions) * 10  # 10x structuring for realism
        normal_txns = self.generate_normal_transactions(
            accounts=all_accounts,
            num_transactions=num_normal_txns,
            start_date=start_date,
            end_date=end_date,
        )
        self.transactions.extend(normal_txns)

        # Summary statistics
        structuring_txns = [
            t for t in self.transactions if t.get("suspicious_pattern") == "structuring"
        ]

        print("\n✅ Data generation complete!")
        print("\nStatistics:")
        print(f"  Persons: {len(self.persons)}")
        print(f"  Accounts: {len(self.accounts)}")
        print(f"  Addresses: {len(self.addresses)}")
        print(f"  Phones: {len(self.phones)}")
        print(f"  Total Transactions: {len(self.transactions)}")
        print(f"  Structuring Transactions: {len(structuring_txns)}")
        print(f"  Normal Transactions: {len(self.transactions) - len(structuring_txns)}")
        print(f"  Beneficiary Accounts: {len(beneficiary_accounts)}")
        print(f"  Mule Accounts: {len(all_mule_accounts)}")

        return {
            "persons": self.persons,
            "accounts": self.accounts,
            "transactions": self.transactions,
            "addresses": self.addresses,
            "phones": self.phones,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "num_structuring_patterns": self.num_beneficiaries,
                "num_mule_accounts_per_pattern": self.num_mule_accounts,
                "time_window_hours": self.time_window_hours,
            },
        }

    def export_to_json(self, filename="aml_structuring_data.json"):
        """Export all data to JSON file"""
        data = {
            "persons": self.persons,
            "accounts": self.accounts,
            "transactions": self.transactions,
            "addresses": self.addresses,
            "phones": self.phones,
        }

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        print(f"\n💾 Data exported to {filename}")

    def export_to_csv(self, prefix="aml_data"):
        """Export data to separate CSV files"""
        import csv

        # Export persons
        with open(f"{prefix}_persons.csv", "w", newline="") as f:
            if self.persons:
                writer = csv.DictWriter(f, fieldnames=self.persons[0].keys())
                writer.writeheader()
                writer.writerows(self.persons)

        # Export accounts
        with open(f"{prefix}_accounts.csv", "w", newline="") as f:
            if self.accounts:
                writer = csv.DictWriter(f, fieldnames=self.accounts[0].keys())
                writer.writeheader()
                writer.writerows(self.accounts)

        # Export transactions
        with open(f"{prefix}_transactions.csv", "w", newline="") as f:
            if self.transactions:
                writer = csv.DictWriter(f, fieldnames=self.transactions[0].keys())
                writer.writeheader()
                writer.writerows(self.transactions)

        # Export addresses
        with open(f"{prefix}_addresses.csv", "w", newline="") as f:
            if self.addresses:
                writer = csv.DictWriter(f, fieldnames=self.addresses[0].keys())
                writer.writeheader()
                writer.writerows(self.addresses)

        # Export phones
        with open(f"{prefix}_phones.csv", "w", newline="") as f:
            if self.phones:
                writer = csv.DictWriter(f, fieldnames=self.phones[0].keys())
                writer.writeheader()
                writer.writerows(self.phones)

        print(f"\n💾 Data exported to CSV files ({prefix}_*.csv)")


def main():
    """Main execution"""
    print("=" * 60)
    print("AML Structuring Pattern - Synthetic Data Generator")
    print("=" * 60)
    print()

    # Configure generator
    generator = AMLDataGenerator(
        num_normal_customers=50,  # Normal customers (noise)
        num_mule_accounts=10,  # Mule accounts per structuring ring
        num_beneficiaries=2,  # Beneficiary accounts (launderers)
        time_window_hours=24,  # Coordination time window
    )

    # Generate all data
    data = generator.generate_all_data()

    # Export to both JSON and CSV
    generator.export_to_json("banking/data/aml/aml_structuring_data.json")
    generator.export_to_csv("banking/data/aml/aml_data")

    print("\n" + "=" * 60)
    print("✅ Generation complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

# Signature: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
