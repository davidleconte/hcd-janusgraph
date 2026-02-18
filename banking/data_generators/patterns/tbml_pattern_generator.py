"""
Trade-Based Money Laundering (TBML) Pattern Generator

Generates sophisticated TBML patterns with 20+ indicators including over/under-invoicing,
phantom shipping, multiple invoicing, and goods misclassification.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ..core.base_generator import BaseGenerator
from ..events.document_generator import DocumentGenerator
from ..events.transaction_generator import TransactionGenerator
from ..utils.constants import COUNTRIES, TAX_HAVENS
from ..utils.data_models import Pattern, RiskLevel
from ..utils.deterministic import REFERENCE_TIMESTAMP
from ..utils.helpers import (
    calculate_pattern_confidence,
    is_tax_haven,
    random_choice_weighted,
    random_datetime_between,
)


class TBMLPatternGenerator(BaseGenerator[Pattern]):
    """
    Generates Trade-Based Money Laundering patterns with comprehensive indicators.

    Features:
    - 20+ TBML indicators
    - Over-invoicing detection (inflated prices)
    - Under-invoicing detection (deflated prices)
    - Phantom shipping (no actual goods)
    - Multiple invoicing (same goods invoiced multiple times)
    - Short shipping (invoice for more than shipped)
    - Goods misclassification
    - Trade route analysis
    - Price variance detection
    - Volume anomaly detection

    Pattern Types:
    1. Over-invoicing: Inflated prices to move money
    2. Under-invoicing: Deflated prices to evade duties
    3. Phantom shipping: Invoices without actual goods
    4. Multiple invoicing: Same shipment invoiced multiple times
    5. Carousel fraud: Circular trading patterns

    Use Cases:
    - Customs fraud detection
    - Money laundering investigation
    - Trade compliance monitoring
    - Supply chain integrity
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TBMLPatternGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Initialize sub-generators
        self.doc_gen = DocumentGenerator(seed=seed, locale=locale, config=config)
        self.txn_gen = TransactionGenerator(seed=seed, locale=locale, config=config)

        # Pattern type distribution
        self.pattern_type_weights = {
            "over_invoicing": 0.30,
            "under_invoicing": 0.25,
            "phantom_shipping": 0.20,
            "multiple_invoicing": 0.15,
            "carousel_fraud": 0.10,
        }

        # High-risk trade routes (involving tax havens or high-risk countries)
        self.high_risk_routes = self._generate_high_risk_routes()

    def generate(
        self,
        pattern_type: Optional[str] = None,
        entity_count: Optional[int] = None,
        document_count: Optional[int] = None,
        transaction_count: Optional[int] = None,
        duration_days: Optional[int] = None,
        existing_entity_ids: Optional[List[str]] = None,
    ) -> Tuple[Pattern, List[Any], List[Any]]:
        """
        Generate a single TBML pattern.

        Args:
            pattern_type: Type of TBML pattern
            entity_count: Number of entities involved (2-5)
            document_count: Number of documents (3-20)
            transaction_count: Number of transactions (3-20)
            duration_days: Duration of pattern (30-180 days)

        Returns:
            Tuple containing:
            - Pattern object
            - List of generated Transaction objects
            - List of generated Document objects
        """
        # Select pattern type
        if pattern_type is None:
            pattern_type = random_choice_weighted(list(self.pattern_type_weights.items()))

        # Type assertion for type checker
        assert pattern_type is not None, "pattern_type must be set"

        # Set defaults
        if entity_count is None:
            entity_count = random.randint(2, 5)
        if document_count is None:
            document_count = random.randint(3, 20)
        if transaction_count is None:
            transaction_count = random.randint(3, 20)
        if duration_days is None:
            duration_days = random.randint(30, 180)

        # Generate pattern dates
        end_date = REFERENCE_TIMESTAMP
        start_date = end_date - timedelta(days=duration_days)
        # Generate entities involved (or select from existing)
        if existing_entity_ids:
            sample_count = min(entity_count, len(existing_entity_ids))
            entity_ids = random.sample(existing_entity_ids, sample_count)
            if sample_count < entity_count:
                entity_ids.extend(
                    [f"COM-{self.faker.uuid4()[:8]}" for _ in range(entity_count - sample_count)]
                )
        else:
            entity_ids = [f"COM-{self.faker.uuid4()[:8]}" for _ in range(entity_count)]
        entity_ids = [f"COM-{self.faker.uuid4()[:8]}" for _ in range(entity_count)]
        # Generate documents
        documents = self._generate_pattern_documents(
            entity_ids, document_count, start_date, end_date, pattern_type
        )

        # Generate transactions
        transactions = self._generate_pattern_transactions(
            entity_ids, transaction_count, start_date, end_date, documents
        )

        # Calculate pattern characteristics
        total_value: Decimal
        if transactions:
            total_value = sum((Decimal(str(t.amount)) for t in transactions), Decimal("0.00"))
        else:
            total_value = Decimal("0.00")

        # Generate indicators
        indicators = self._generate_tbml_indicators(
            pattern_type, documents, transactions, entity_ids
        )

        # Generate red flags
        red_flags = self._generate_red_flags(pattern_type, documents, transactions, total_value)

        # Calculate confidence score
        confidence_score = calculate_pattern_confidence(
            indicators, red_flags, total_value, duration_days
        )

        # Determine risk level
        risk_level = self._determine_risk_level(confidence_score, total_value)

        # Calculate severity score
        severity_score = self._calculate_severity_score(
            confidence_score, total_value, len(indicators), len(red_flags)
        )

        pattern = Pattern(
            pattern_id=f"PTN-TBML-{self.faker.uuid4()[:12]}",
            pattern_type="tbml",
            detection_date=REFERENCE_TIMESTAMP,
            detection_method=f"tbml_analysis_{pattern_type}",
            confidence_score=confidence_score,
            entity_ids=entity_ids,
            entity_types=["company"] * entity_count,
            transaction_ids=[t.id for t in transactions],
            communication_ids=[],  # TBML primarily document-based
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days,
            total_value=total_value,
            transaction_count=len(transactions),
            risk_level=risk_level,
            severity_score=severity_score,
            indicators=indicators,
            red_flags=red_flags,
            is_investigated=False,
            investigation_status=None,
            investigator_id=None,
            investigation_notes=None,
            is_confirmed=None,
            outcome=None,
            action_taken=None,
            metadata={
                "pattern_subtype": pattern_type,
                "document_count": len(documents),
                "entity_count": entity_count,
                "average_document_value": (
                    float(sum(d.total_amount for d in documents) / len(documents))
                    if documents
                    else 0
                ),
                "average_transaction_value": (
                    float(total_value / len(transactions)) if transactions else 0
                ),
                "high_risk_route": (
                    random.choice(self.high_risk_routes) if random.random() < 0.5 else None
                ),
                "price_variance_percentage": (
                    random.uniform(50, 500)
                    if pattern_type in ["over_invoicing", "under_invoicing"]
                    else 0
                ),
            },
        )

        return pattern, transactions, documents

    def _generate_high_risk_routes(self) -> List[Dict[str, str]]:
        """Generate list of high-risk trade routes."""
        routes = []
        tax_haven_list = list(TAX_HAVENS)

        # Routes involving tax havens
        for haven in tax_haven_list[:10]:  # Top 10 tax havens
            routes.append(
                {
                    "origin": random.choice(list(COUNTRIES.keys())),
                    "destination": haven,
                    "risk_factor": "tax_haven_destination",
                }
            )
            routes.append(
                {
                    "origin": haven,
                    "destination": random.choice(list(COUNTRIES.keys())),
                    "risk_factor": "tax_haven_origin",
                }
            )

        return routes

    def _generate_pattern_documents(
        self,
        entity_ids: List[str],
        document_count: int,
        start_date: datetime,
        end_date: datetime,
        pattern_type: str,
    ) -> List[Any]:
        """Generate documents forming the TBML pattern."""
        documents = []

        for i in range(document_count):
            # Select issuer and recipient
            issuer_id = random.choice(entity_ids)
            recipient_id = random.choice([e for e in entity_ids if e != issuer_id])

            # Generate document date
            doc_date = random_datetime_between(start_date, end_date)

            # Generate document with TBML indicators
            doc = self.doc_gen.generate(
                issuer_id=issuer_id, recipient_id=recipient_id, force_tbml=True
            )

            # Override date
            doc.issue_date = doc_date

            # Add pattern-specific metadata
            doc.metadata["pattern_type"] = pattern_type
            doc.metadata["pattern_sequence"] = i + 1
            doc.metadata["pattern_total_documents"] = document_count

            # Pattern-specific adjustments
            if pattern_type == "over_invoicing":
                # Inflate prices
                for item in doc.line_items:
                    item["unit_price"] *= random.uniform(2, 10)
                    item["amount"] = item["quantity"] * item["unit_price"]
                doc.total_amount = sum(
                    (Decimal(str(item["amount"])) for item in doc.line_items), Decimal("0.00")
                )
                doc.metadata["price_inflation_factor"] = random.uniform(2, 10)

            elif pattern_type == "under_invoicing":
                # Deflate prices
                for item in doc.line_items:
                    item["unit_price"] *= random.uniform(0.1, 0.5)
                    item["amount"] = item["quantity"] * item["unit_price"]
                doc.total_amount = sum(
                    (Decimal(str(item["amount"])) for item in doc.line_items), Decimal("0.00")
                )
                doc.metadata["price_deflation_factor"] = random.uniform(0.1, 0.5)

            elif pattern_type == "phantom_shipping":
                doc.metadata["actual_shipment"] = False
                doc.metadata["phantom_indicator"] = True

            elif pattern_type == "multiple_invoicing":
                # Same shipment ID for multiple invoices
                if i > 0:
                    doc.metadata["shipment_id"] = documents[0].metadata.get(
                        "shipment_id", f"SHIP-{self.faker.uuid4()[:8]}"
                    )
                else:
                    doc.metadata["shipment_id"] = f"SHIP-{self.faker.uuid4()[:8]}"

            documents.append(doc)

        return documents

    def _generate_pattern_transactions(
        self,
        entity_ids: List[str],
        transaction_count: int,
        start_date: datetime,
        end_date: datetime,
        documents: List[Any],
    ) -> List[Any]:
        """Generate transactions associated with TBML pattern."""
        transactions = []

        for i in range(transaction_count):
            # Select from/to entities
            from_entity = random.choice(entity_ids)
            to_entity = random.choice([e for e in entity_ids if e != from_entity])

            # Transaction date (after corresponding document)
            if i < len(documents):
                min_date = documents[i].issue_date
            else:
                min_date = start_date
            txn_date = random_datetime_between(min_date, end_date)

            # Generate transaction
            txn = self.txn_gen.generate(
                from_account_id=f"ACC-{from_entity[-8:]}", to_account_id=f"ACC-{to_entity[-8:]}"
            )

            # Override date
            txn.transaction_date = txn_date

            # Link to document if available
            if i < len(documents):
                txn.metadata["related_document_id"] = documents[i].document_id
                txn.metadata["document_amount"] = float(documents[i].total_amount)

            transactions.append(txn)

        return transactions

    def _generate_tbml_indicators(
        self,
        pattern_type: str,
        documents: List[Any],
        transactions: List[Any],
        entity_ids: List[str],
    ) -> List[str]:
        """Generate TBML indicators."""
        indicators = [
            "trade_based_money_laundering_suspected",
            "unusual_trade_patterns",
            "document_anomalies",
        ]

        if pattern_type == "over_invoicing":
            indicators.extend(
                [
                    "over_invoicing_detected",
                    "inflated_prices",
                    "price_variance_exceeds_threshold",
                    "market_price_deviation",
                ]
            )

        elif pattern_type == "under_invoicing":
            indicators.extend(
                [
                    "under_invoicing_detected",
                    "deflated_prices",
                    "below_market_pricing",
                    "duty_evasion_suspected",
                ]
            )

        elif pattern_type == "phantom_shipping":
            indicators.extend(
                [
                    "phantom_shipping_detected",
                    "no_actual_goods_movement",
                    "documentation_only_transaction",
                    "fictitious_trade",
                ]
            )

        elif pattern_type == "multiple_invoicing":
            indicators.extend(
                [
                    "multiple_invoicing_detected",
                    "duplicate_shipment_references",
                    "same_goods_invoiced_multiple_times",
                    "invoice_duplication",
                ]
            )

        elif pattern_type == "carousel_fraud":
            indicators.extend(
                [
                    "carousel_fraud_detected",
                    "circular_trading_pattern",
                    "goods_moving_in_circle",
                    "vat_fraud_suspected",
                ]
            )

        # Additional indicators based on characteristics
        if len(documents) > 10:
            indicators.append("high_volume_trade_activity")

        if len(entity_ids) >= 4:
            indicators.append("multiple_entities_involved")

        # Check for tax haven involvement
        for doc in documents:
            if "origin_country" in doc.metadata:
                if is_tax_haven(doc.metadata["origin_country"]):
                    indicators.append("tax_haven_origin")
                    break
            if "destination_country" in doc.metadata:
                if is_tax_haven(doc.metadata["destination_country"]):
                    indicators.append("tax_haven_destination")
                    break

        return list(set(indicators))  # Remove duplicates

    def _generate_red_flags(
        self, pattern_type: str, documents: List[Any], transactions: List[Any], total_value: Decimal
    ) -> List[str]:
        """Generate red flags."""
        red_flags = []

        # High value
        if total_value > 10000000:
            red_flags.append("very_high_transaction_value")
        elif total_value > 5000000:
            red_flags.append("high_transaction_value")

        # Document-transaction mismatch
        if len(documents) != len(transactions):
            red_flags.append("document_transaction_count_mismatch")

        # High volume
        if len(documents) > 15:
            red_flags.append("unusually_high_document_volume")

        # Pattern-specific red flags
        if pattern_type == "over_invoicing":
            red_flags.extend(["significant_price_inflation", "money_movement_suspected"])

        elif pattern_type == "under_invoicing":
            red_flags.extend(["customs_duty_evasion_suspected", "tax_evasion_indicator"])

        elif pattern_type == "phantom_shipping":
            red_flags.extend(["no_physical_goods_movement", "paper_transaction_only"])

        elif pattern_type == "multiple_invoicing":
            red_flags.extend(["invoice_fraud_suspected", "duplicate_billing"])

        return red_flags

    def _determine_risk_level(self, confidence_score: float, total_value: Decimal) -> RiskLevel:
        """Determine risk level."""
        if confidence_score >= 0.8 and total_value > 10000000:
            return RiskLevel.CRITICAL
        elif confidence_score >= 0.7 or total_value > 5000000:
            return RiskLevel.HIGH
        elif confidence_score >= 0.5 or total_value > 1000000:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _calculate_severity_score(
        self,
        confidence_score: float,
        total_value: Decimal,
        indicator_count: int,
        red_flag_count: int,
    ) -> float:
        """Calculate severity score (0-1)."""
        score = confidence_score * 0.4  # Base from confidence

        # Value component
        if total_value > 10000000:
            score += 0.3
        elif total_value > 5000000:
            score += 0.2
        elif total_value > 1000000:
            score += 0.1

        # Indicator count component
        if indicator_count >= 10:
            score += 0.2
        elif indicator_count >= 5:
            score += 0.1

        # Red flag component
        if red_flag_count >= 5:
            score += 0.1

        return min(score, 1.0)

    def generate_complex_tbml_network(
        self, network_size: int = 5, document_count: int = 20, duration_days: int = 180
    ) -> Tuple[Pattern, List[Any], List[Any]]:
        """
        Generate a complex TBML network with multiple entities and documents.

        Args:
            network_size: Number of companies in network
            document_count: Total number of documents
            duration_days: Duration of pattern

        Returns:
            Tuple containing:
            - Pattern object
            - List of generated Transaction objects
            - List of generated Document objects
        """
        return self.generate(
            pattern_type="carousel_fraud",
            entity_count=network_size,
            document_count=document_count,
            transaction_count=document_count,
            duration_days=duration_days,
        )
