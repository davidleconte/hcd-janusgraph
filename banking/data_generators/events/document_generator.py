"""
Document Generator for Banking Compliance Use Cases

Generates realistic business documents (invoices, contracts, reports) with
Trade-Based Money Laundering (TBML) indicators for compliance monitoring.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone

from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import Field

from ..core.base_generator import BaseGenerator
from ..utils.constants import COUNTRIES
from ..utils.data_models import BaseEntity
from ..utils.helpers import random_amount, random_choice_weighted, random_datetime_between


class Document(BaseEntity):
    """Business document entity"""

    document_id: str
    document_type: str
    issuer_id: str
    recipient_id: str
    issue_date: datetime
    document_number: str
    currency: str
    total_amount: Decimal
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    tbml_indicators: List[str] = Field(default_factory=list)
    authenticity_score: float = 1.0  # 0-1 scale (1 = authentic)
    risk_score: float = 0.0
    flagged_for_review: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentGenerator(BaseGenerator[Document]):
    """
    Generates realistic business documents with TBML indicators.

    Features:
    - Multiple document types (invoice, contract, bill of lading, etc.)
    - Trade-Based Money Laundering (TBML) indicators
    - Over/under-invoicing detection
    - Phantom shipping detection
    - Multiple invoicing detection
    - Document authenticity scoring

    Use Cases:
    - Trade-Based Money Laundering detection
    - Invoice fraud detection
    - Supply chain compliance
    - Customs fraud detection
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize DocumentGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Document type distribution
        self.document_type_weights = {
            "invoice": 0.40,
            "purchase_order": 0.20,
            "bill_of_lading": 0.15,
            "contract": 0.10,
            "customs_declaration": 0.08,
            "certificate_of_origin": 0.05,
            "packing_list": 0.02,
        }

        # Product categories for line items
        self.product_categories = [
            "Electronics",
            "Textiles",
            "Machinery",
            "Chemicals",
            "Pharmaceuticals",
            "Automotive Parts",
            "Food Products",
            "Raw Materials",
            "Consumer Goods",
            "Industrial Equipment",
        ]

        # TBML probability
        self.tbml_probability = config.get("tbml_probability", 0.05) if config else 0.05

    def generate(
        self,
        issuer_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        document_type: Optional[str] = None,
        force_tbml: bool = False,
    ) -> Document:
        """
        Generate a single document.

        Args:
            issuer_id: ID of issuer (company)
            recipient_id: ID of recipient (company)
            document_type: Type of document
            force_tbml: Force TBML indicators

        Returns:
            Document object with all attributes
        """
        # Generate IDs if not provided
        if issuer_id is None:
            issuer_id = f"COM-{self.faker.uuid4()[:8]}"
        if recipient_id is None:
            recipient_id = f"COM-{self.faker.uuid4()[:8]}"

        # Select document type (ensure not None)
        if document_type is None:
            document_type = random_choice_weighted(list(self.document_type_weights.items()))

        # Generate issue date
        issue_date = random_datetime_between(
            REFERENCE_TIMESTAMP - timedelta(days=180), REFERENCE_TIMESTAMP
        )

        # Generate document number
        document_number = self._generate_document_number(document_type)

        # Select currency
        currency = random_choice_weighted(
            [
                ("USD", 0.50),
                ("EUR", 0.20),
                ("GBP", 0.10),
                ("CNY", 0.08),
                ("JPY", 0.05),
                ("CHF", 0.07),
            ]
        )

        # Determine if TBML
        is_tbml = force_tbml or random.random() < self.tbml_probability

        # Generate line items
        line_items = self._generate_line_items(currency, is_tbml)

        # Calculate total amount
        total_amount = (
            sum(Decimal(str(item["amount"])) for item in line_items)
            if line_items
            else Decimal("0.00")
        )

        # Generate TBML indicators
        tbml_indicators = []
        if is_tbml:
            tbml_indicators = self._generate_tbml_indicators(
                document_type, line_items, total_amount
            )

        # Calculate authenticity score (lower if TBML)
        authenticity_score = self._calculate_authenticity_score(
            document_type, line_items, tbml_indicators
        )

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            document_type, total_amount, tbml_indicators, authenticity_score
        )

        # Generate metadata
        metadata = self._generate_metadata(document_type, currency, is_tbml)

        # Determine if flagged
        flagged_for_review = risk_score > 0.6 or len(tbml_indicators) > 2

        return Document(
            document_id=f"DOC-{self.faker.uuid4()[:12]}",
            document_type=document_type,
            issuer_id=issuer_id,
            recipient_id=recipient_id,
            issue_date=issue_date,
            document_number=document_number,
            currency=currency,
            total_amount=total_amount,
            line_items=line_items,
            tbml_indicators=tbml_indicators,
            authenticity_score=authenticity_score,
            risk_score=risk_score,
            flagged_for_review=flagged_for_review,
            metadata=metadata,
        )

    def _generate_document_number(self, document_type: str) -> str:
        """Generate realistic document number."""
        prefix_map = {
            "invoice": "INV",
            "purchase_order": "PO",
            "bill_of_lading": "BOL",
            "contract": "CTR",
            "customs_declaration": "CUS",
            "certificate_of_origin": "COO",
            "packing_list": "PKL",
        }
        prefix = prefix_map.get(document_type, "DOC")
        number = random.randint(100000, 999999)
        year = REFERENCE_TIMESTAMP.year
        return f"{prefix}-{year}-{number}"

    def _generate_line_items(self, currency: str, is_tbml: bool) -> List[Dict[str, Any]]:
        """Generate document line items."""
        num_items = random.randint(1, 10)
        line_items = []

        for i in range(num_items):
            category = random.choice(self.product_categories)
            description = f"{self.faker.word().capitalize()} {category}"
            quantity = random.randint(1, 1000)

            # Unit price (manipulated if TBML)
            if is_tbml and random.random() < 0.5:
                # Over-invoicing or under-invoicing
                if random.random() < 0.5:
                    # Over-invoice (2-10x normal price)
                    unit_price = float(random_amount(100, 1000)) * random.uniform(2, 10)
                else:
                    # Under-invoice (10-50% of normal price)
                    unit_price = float(random_amount(100, 1000)) * random.uniform(0.1, 0.5)
            else:
                unit_price = float(random_amount(10, 1000))

            amount = quantity * unit_price

            line_items.append(
                {
                    "line_number": i + 1,
                    "description": description,
                    "category": category,
                    "quantity": quantity,
                    "unit_price": round(unit_price, 2),
                    "amount": round(amount, 2),
                    "currency": currency,
                }
            )

        return line_items

    def _generate_tbml_indicators(
        self, document_type: str, line_items: List[Dict[str, Any]], total_amount: Decimal
    ) -> List[str]:
        """Generate TBML indicators."""
        indicators = []

        # Over-invoicing detection
        avg_unit_price = sum(item["unit_price"] for item in line_items) / len(line_items)
        if avg_unit_price > 5000:
            indicators.append("over_invoicing_suspected")

        # Under-invoicing detection
        if avg_unit_price < 10:
            indicators.append("under_invoicing_suspected")

        # Unusual quantity
        total_quantity = sum(item["quantity"] for item in line_items)
        if total_quantity > 10000:
            indicators.append("unusual_quantity")

        # Phantom shipping (no actual goods)
        if random.random() < 0.2:
            indicators.append("phantom_shipping_suspected")

        # Multiple invoicing (same goods invoiced multiple times)
        if random.random() < 0.15:
            indicators.append("multiple_invoicing_suspected")

        # Misclassification of goods
        if random.random() < 0.2:
            indicators.append("goods_misclassification_suspected")

        # Short shipping (invoice for more than shipped)
        if random.random() < 0.15:
            indicators.append("short_shipping_suspected")

        # Unusual payment terms
        if random.random() < 0.1:
            indicators.append("unusual_payment_terms")

        return indicators

    def _calculate_authenticity_score(
        self, document_type: str, line_items: List[Dict[str, Any]], tbml_indicators: List[str]
    ) -> float:
        """Calculate document authenticity score (0-1, 1=authentic)."""
        score = 1.0

        # Reduce score for TBML indicators
        score -= len(tbml_indicators) * 0.15

        # Reduce score for suspicious pricing
        for item in line_items:
            if item["unit_price"] > 10000 or item["unit_price"] < 1:
                score -= 0.05

        return max(score, 0.0)

    def _calculate_risk_score(
        self,
        document_type: str,
        total_amount: Decimal,
        tbml_indicators: List[str],
        authenticity_score: float,
    ) -> float:
        """Calculate document risk score (0-1)."""
        score = 0.0

        # TBML indicators (major factor)
        if len(tbml_indicators) > 0:
            score += 0.3
        if len(tbml_indicators) > 2:
            score += 0.2

        # Low authenticity
        if authenticity_score < 0.5:
            score += 0.2

        # High value
        if total_amount > 1000000:
            score += 0.15
        if total_amount > 10000000:
            score += 0.15

        return min(score, 1.0)

    def _generate_metadata(
        self, document_type: str, currency: str, is_tbml: bool
    ) -> Dict[str, Any]:
        """Generate document metadata."""
        metadata: Dict[str, Any] = {
            "document_type": document_type,
            "currency": currency,
            "payment_terms": random.choice(
                ["Net 30", "Net 60", "Net 90", "COD", "Advance Payment"]
            ),
            "shipping_method": random.choice(["Air", "Sea", "Land", "Rail"]),
            "incoterms": random.choice(["FOB", "CIF", "EXW", "DDP", "DAP"]),
        }

        if document_type in ["invoice", "bill_of_lading"]:
            metadata["origin_country"] = random.choice(list(COUNTRIES.keys()))
            metadata["destination_country"] = random.choice(list(COUNTRIES.keys()))

        if is_tbml:
            metadata["price_variance_percentage"] = random.uniform(50, 500)
            metadata["market_price_comparison"] = "significantly_different"

        return metadata

    def generate_tbml_document_set(
        self, issuer_id: str, recipient_id: str, document_count: int = 3
    ) -> List[Document]:
        """
        Generate a set of related documents with TBML indicators.

        Args:
            issuer_id: ID of issuer
            recipient_id: ID of recipient
            document_count: Number of documents

        Returns:
            List of Document objects with TBML indicators
        """
        documents = []
        base_date = REFERENCE_TIMESTAMP - timedelta(days=random.randint(30, 180))

        for i in range(document_count):
            # Generate document with TBML indicators
            doc = self.generate(issuer_id=issuer_id, recipient_id=recipient_id, force_tbml=True)

            # Adjust date to show progression
            doc.issue_date = base_date + timedelta(days=i * 30)

            # Add set metadata
            doc.metadata["document_set_id"] = f"SET-{self.faker.uuid4()[:8]}"
            doc.metadata["set_position"] = i + 1
            doc.metadata["set_total"] = document_count

            documents.append(doc)

        return documents
