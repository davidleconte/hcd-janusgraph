"""
Travel Generator for Banking Compliance Use Cases

Generates realistic international travel events with suspicious pattern detection
for money laundering, sanctions evasion, and coordination analysis.

Author: David LECONTE - IBM Worldwide | Data & AI | Tiger Team | Data Watstonx.Data Global Product Specialist (GPS)
Date: 2026-02-06
"""

import random
from datetime import datetime, timedelta, timezone

from banking.data_generators.utils.deterministic import REFERENCE_TIMESTAMP
from typing import Any, Dict, List, Optional

from pydantic import Field

from ..core.base_generator import BaseGenerator
from ..utils.constants import COUNTRIES, HIGH_RISK_COUNTRIES, TAX_HAVENS
from ..utils.data_models import BaseEntity
from ..utils.helpers import (
    is_high_risk_country,
    is_tax_haven,
    random_choice_weighted,
    random_datetime_between,
)


class TravelEvent(BaseEntity):
    """Travel event entity"""

    travel_id: str
    traveler_id: str
    departure_country: str
    arrival_country: str
    departure_date: datetime
    arrival_date: datetime
    purpose: str
    transport_mode: str
    visa_required: bool
    visa_obtained: bool
    passport_number: Optional[str] = None
    suspicious_indicators: List[str] = Field(default_factory=list)
    risk_score: float = 0.0
    flagged_for_review: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TravelGenerator(BaseGenerator[TravelEvent]):
    """
    Generates realistic international travel events with compliance indicators.

    Features:
    - Multi-country travel patterns
    - High-risk jurisdiction detection
    - Tax haven visits
    - Suspicious travel patterns (frequency, timing, coordination)
    - Visa tracking
    - Multiple transport modes

    Use Cases:
    - Money laundering detection (courier activity)
    - Sanctions evasion monitoring
    - Coordinated activity detection
    - Customer due diligence (CDD)
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        locale: str = "en_US",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TravelGenerator.

        Args:
            seed: Random seed for reproducibility
            locale: Faker locale
            config: Additional configuration options
        """
        super().__init__(seed, locale, config)

        # Travel purpose distribution
        self.purpose_weights = {
            "business": 0.40,
            "tourism": 0.35,
            "family_visit": 0.15,
            "conference": 0.05,
            "medical": 0.03,
            "education": 0.02,
        }

        # Transport mode distribution
        self.transport_weights = {"air": 0.75, "land": 0.15, "sea": 0.05, "rail": 0.05}

        # Suspicious travel probability
        self.suspicious_probability = config.get("suspicious_probability", 0.05) if config else 0.05

    def generate(
        self,
        traveler_id: Optional[str] = None,
        departure_country: Optional[str] = None,
        arrival_country: Optional[str] = None,
        force_suspicious: bool = False,
    ) -> TravelEvent:
        """
        Generate a single travel event.

        Args:
            traveler_id: ID of traveler (person)
            departure_country: Departure country code
            arrival_country: Arrival country code
            force_suspicious: Force suspicious indicators

        Returns:
            TravelEvent object with all attributes
        """
        # Generate traveler ID if not provided
        if traveler_id is None:
            traveler_id = f"PER-{self.faker.uuid4()[:8]}"

        # Select countries
        country_codes = list(COUNTRIES.keys())
        if departure_country is None:
            departure_country = random.choice(country_codes)
        if arrival_country is None:
            # Ensure different from departure
            arrival_country = random.choice([c for c in country_codes if c != departure_country])

        # Generate travel dates
        departure_date = random_datetime_between(
            REFERENCE_TIMESTAMP - timedelta(days=90),
            REFERENCE_TIMESTAMP + timedelta(days=30),
        )

        # Travel duration (1-30 days)
        duration_days = random.randint(1, 30)
        arrival_date = departure_date + timedelta(days=duration_days)

        # Select purpose and transport
        purpose = random_choice_weighted(list(self.purpose_weights.items()))
        transport_mode = random_choice_weighted(list(self.transport_weights.items()))

        # Visa requirements (simplified)
        visa_required = random.random() < 0.3  # 30% require visa
        visa_obtained = (
            True if not visa_required else random.random() < 0.95
        )  # 95% obtain if required

        # Generate passport number
        passport_number = self._generate_passport_number(departure_country)

        # Determine if suspicious
        is_suspicious = force_suspicious or random.random() < self.suspicious_probability

        # Generate suspicious indicators
        suspicious_indicators = []
        if is_suspicious:
            suspicious_indicators = self._generate_suspicious_indicators(
                departure_country, arrival_country, purpose, duration_days
            )

        # Calculate risk score
        risk_score = self._calculate_risk_score(
            departure_country, arrival_country, purpose, duration_days, suspicious_indicators
        )

        # Generate metadata
        metadata = self._generate_metadata(transport_mode, purpose, duration_days, is_suspicious)

        # Determine if flagged
        flagged_for_review = risk_score > 0.6 or len(suspicious_indicators) > 2

        return TravelEvent(
            travel_id=f"TRVL-{self.faker.uuid4()[:12]}",
            traveler_id=traveler_id,
            departure_country=departure_country,
            arrival_country=arrival_country,
            departure_date=departure_date,
            arrival_date=arrival_date,
            purpose=purpose,
            transport_mode=transport_mode,
            visa_required=visa_required,
            visa_obtained=visa_obtained,
            passport_number=passport_number,
            suspicious_indicators=suspicious_indicators,
            risk_score=risk_score,
            flagged_for_review=flagged_for_review,
            metadata=metadata,
        )

    def _generate_passport_number(self, country_code: str) -> str:
        """Generate realistic passport number."""
        if country_code == "US":
            return f"{random.randint(100000000, 999999999)}"
        elif country_code == "GB":
            return f"{random.randint(100000000, 999999999)}"
        else:
            # Generic format
            prefix = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=2))
            number = "".join(random.choices("0123456789", k=7))
            return f"{prefix}{number}"

    def _generate_suspicious_indicators(
        self, departure_country: str, arrival_country: str, purpose: str, duration_days: int
    ) -> List[str]:
        """Generate suspicious travel indicators."""
        indicators = []

        # High-risk country involvement
        if is_high_risk_country(departure_country):
            indicators.append("departure_from_high_risk_country")
        if is_high_risk_country(arrival_country):
            indicators.append("arrival_in_high_risk_country")

        # Tax haven involvement
        if is_tax_haven(departure_country):
            indicators.append("departure_from_tax_haven")
        if is_tax_haven(arrival_country):
            indicators.append("arrival_in_tax_haven")

        # Short duration in high-risk area
        if duration_days <= 2 and (
            is_high_risk_country(arrival_country) or is_tax_haven(arrival_country)
        ):
            indicators.append("brief_visit_to_sensitive_location")

        # Unusual purpose for destination
        if purpose == "tourism" and is_high_risk_country(arrival_country):
            indicators.append("tourism_to_high_risk_country")

        # Frequent traveler pattern (would need historical data)
        if random.random() < 0.2:
            indicators.append("frequent_international_travel")

        # Cash courier indicators
        if random.random() < 0.1:
            indicators.append("potential_cash_courier")

        return indicators

    def _calculate_risk_score(
        self,
        departure_country: str,
        arrival_country: str,
        purpose: str,
        duration_days: int,
        suspicious_indicators: List[str],
    ) -> float:
        """Calculate travel risk score (0-1)."""
        score = 0.0

        # Suspicious indicators (major factor)
        if len(suspicious_indicators) > 0:
            score += 0.3
        if len(suspicious_indicators) > 2:
            score += 0.2

        # High-risk countries
        if is_high_risk_country(departure_country) or is_high_risk_country(arrival_country):
            score += 0.2

        # Tax havens
        if is_tax_haven(departure_country) or is_tax_haven(arrival_country):
            score += 0.15

        # Very short trips
        if duration_days <= 2:
            score += 0.1

        # Business purpose to high-risk area
        if purpose == "business" and is_high_risk_country(arrival_country):
            score += 0.05

        return min(score, 1.0)

    def _generate_metadata(
        self, transport_mode: str, purpose: str, duration_days: int, is_suspicious: bool
    ) -> Dict[str, Any]:
        """Generate travel metadata."""
        metadata: Dict[str, Any] = {
            "transport_mode": transport_mode,
            "purpose": purpose,
            "duration_days": duration_days,
            "booking_date": (
                REFERENCE_TIMESTAMP - timedelta(days=random.randint(1, 60))
            ).isoformat(),
        }

        if transport_mode == "air":
            metadata["flight_number"] = (
                f"{random.choice(['AA', 'BA', 'LH', 'AF', 'UA'])}{random.randint(100, 9999)}"
            )
            metadata["airline"] = random.choice(
                ["American", "British Airways", "Lufthansa", "Air France", "United"]
            )

        if is_suspicious:
            metadata["travel_frequency_30d"] = random.randint(3, 10)
            metadata["cash_declaration"] = random.random() < 0.3
            if metadata["cash_declaration"]:
                metadata["declared_cash_amount"] = random.randint(5000, 50000)

        return metadata

    def generate_suspicious_travel_pattern(
        self, traveler_id: str, trip_count: int = 5, time_window_days: int = 90
    ) -> List[TravelEvent]:
        """
        Generate a suspicious travel pattern (frequent trips to high-risk areas).

        Args:
            traveler_id: ID of traveler
            trip_count: Number of trips
            time_window_days: Time window for trips

        Returns:
            List of TravelEvent objects forming suspicious pattern
        """
        travels = []
        base_date = REFERENCE_TIMESTAMP - timedelta(days=time_window_days)

        # Select high-risk or tax haven destinations
        risky_destinations = list(HIGH_RISK_COUNTRIES) + list(TAX_HAVENS)

        for i in range(trip_count):
            # Distribute trips across time window
            days_offset = (i / trip_count) * time_window_days

            # Generate travel with suspicious indicators
            travel = self.generate(
                traveler_id=traveler_id,
                arrival_country=random.choice(risky_destinations),
                force_suspicious=True,
            )

            # Adjust date to fit pattern
            travel.departure_date = base_date + timedelta(days=days_offset)
            travel.arrival_date = travel.departure_date + timedelta(days=random.randint(1, 5))

            # Add pattern metadata
            travel.metadata["pattern_trip_number"] = i + 1
            travel.metadata["pattern_total_trips"] = trip_count
            travel.metadata["pattern_time_window_days"] = time_window_days

            travels.append(travel)

        return travels
