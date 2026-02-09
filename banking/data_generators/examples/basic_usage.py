"""
Basic Usage Example for Synthetic Data Generators
==================================================

Demonstrates how to use the Person, Company, and Account generators
to create realistic synthetic data.

Author: David Leconte, IBM Worldwide | Tiger-Team, Watsonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from banking.data_generators.core import AccountGenerator, CompanyGenerator, PersonGenerator


def main():
    """Main example function."""

    print("=" * 80)
    print("Synthetic Data Generation - Basic Usage Example")
    print("=" * 80)
    print()

    # ========================================================================
    # 1. Generate Persons
    # ========================================================================
    print("1. Generating Persons...")
    print("-" * 80)

    person_gen = PersonGenerator(seed=42, locale="en_US")

    # Generate single person
    person = person_gen.generate()
    print("Generated Person:")
    print(f"  Name: {person.full_name}")
    print(f"  Age: {person.age}")
    print(f"  Nationality: {person.nationality}")
    print(f"  Risk Level: {person.risk_level.value}")
    print(
        f"  Annual Income: ${person.annual_income:,.2f}"
        if person.annual_income
        else "  Annual Income: N/A"
    )
    print(f"  Is PEP: {person.is_pep}")
    print(f"  Is Sanctioned: {person.is_sanctioned}")
    print()

    # Generate batch
    print("Generating batch of 10 persons...")
    people = person_gen.generate_batch(count=10, show_progress=False)
    print(f"Generated {len(people)} persons")

    # Show statistics
    stats = person_gen.get_statistics()
    print("Generation Statistics:")
    print(f"  Total Generated: {stats['generated_count']}")
    print(f"  Errors: {stats['error_count']}")
    if stats["generation_rate_per_second"]:
        print(f"  Rate: {stats['generation_rate_per_second']:.2f} persons/sec")
    print()

    # ========================================================================
    # 2. Generate Companies
    # ========================================================================
    print("2. Generating Companies...")
    print("-" * 80)

    company_gen = CompanyGenerator(seed=42, locale="en_US")

    # Generate single company
    company = company_gen.generate()
    print("Generated Company:")
    print(f"  Name: {company.legal_name}")
    print(f"  Type: {company.company_type.value}")
    print(f"  Industry: {company.industry.value}")
    print(f"  Country: {company.registration_country}")
    print(
        f"  Employees: {company.employee_count:,}" if company.employee_count else "  Employees: N/A"
    )
    print(
        f"  Revenue: ${company.annual_revenue:,.2f}" if company.annual_revenue else "  Revenue: N/A"
    )
    print(f"  Is Public: {company.is_public}")
    print(f"  Risk Level: {company.risk_level.value}")
    print(f"  Is Shell Company: {company.is_shell_company}")
    print()

    # Generate batch
    print("Generating batch of 5 companies...")
    companies = company_gen.generate_batch(count=5, show_progress=False)
    print(f"Generated {len(companies)} companies")
    print()

    # ========================================================================
    # 3. Generate Accounts
    # ========================================================================
    print("3. Generating Accounts...")
    print("-" * 80)

    account_gen = AccountGenerator(seed=42, locale="en_US")

    # Generate account for a person
    account = account_gen.generate(owner_id=person.id, owner_type="person")
    print("Generated Account:")
    print(f"  Account Number: {account.account_number}")
    print(f"  Type: {account.account_type.value}")
    print(f"  Currency: {account.currency}")
    print(f"  Bank: {account.bank_name}")
    print(f"  Balance: {account.currency} {account.current_balance:,.2f}")
    print(f"  Status: {account.status}")
    print(f"  Risk Level: {account.risk_level.value}")
    print(f"  Is Monitored: {account.is_monitored}")
    print(f"  Transaction Count: {account.transaction_count:,}")
    print()

    # Generate batch
    print("Generating batch of 5 accounts...")
    accounts = account_gen.generate_batch(count=5, show_progress=False)
    print(f"Generated {len(accounts)} accounts")
    print()

    # ========================================================================
    # 4. Summary
    # ========================================================================
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total Persons Generated: {len(people) + 1}")
    print(f"Total Companies Generated: {len(companies) + 1}")
    print(f"Total Accounts Generated: {len(accounts) + 1}")
    print()

    # Risk distribution
    print("Risk Distribution (Persons):")
    risk_counts = {}
    for p in people + [person]:
        risk_counts[p.risk_level.value] = risk_counts.get(p.risk_level.value, 0) + 1
    for risk, count in sorted(risk_counts.items()):
        print(f"  {risk}: {count}")
    print()

    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
