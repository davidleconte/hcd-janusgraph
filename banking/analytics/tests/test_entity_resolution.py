"""
Unit tests for entity resolution confidence calibration (FR-023).
"""

from unittest.mock import Mock

from banking.analytics.entity_resolution import EntityResolver, ResolutionComplexity


def test_standard_resolution_tax_id_match_drives_high_confidence():
    """Tax ID match should produce high confidence even with slight name variance."""
    resolver = EntityResolver(client=Mock())

    entity_a = {
        "id": "P-001",
        "taxId": "TAX-123",
        "name": "John Doe",
        "dateOfBirth": "1980-01-10",
    }
    entity_b = {
        "id": "P-002",
        "taxId": "TAX-123",
        "name": "Jon Doe",
        "dateOfBirth": "1980-01-11",
    }

    resolver._fetch_entity = Mock(side_effect=[entity_a, entity_b])  # type: ignore[attr-defined]

    match = resolver.resolve(
        entity_a_id="P-001",
        entity_b_id="P-002",
        complexity=ResolutionComplexity.STANDARD,
    )

    assert match.confidence > 0.70
    assert match.resolution_action in {"merge", "link"}
    tax_signal = next(signal for signal in match.match_signals if signal.attribute == "taxId")
    assert "weighted contribution" in tax_signal.explanation


def test_standard_resolution_mismatched_strong_ids_requires_review_or_separate():
    """Mismatched strong identity attributes should not auto-merge."""
    resolver = EntityResolver(client=Mock())

    entity_a = {
        "id": "P-101",
        "taxId": "TAX-AAA",
        "ssn": "111-22-3333",
        "name": "Alice Johnson",
        "dateOfBirth": "1990-02-20",
    }
    entity_b = {
        "id": "P-202",
        "taxId": "TAX-BBB",
        "ssn": "999-88-7777",
        "name": "Alice Jonson",
        "dateOfBirth": "1990-02-21",
    }

    resolver._fetch_entity = Mock(side_effect=[entity_a, entity_b])  # type: ignore[attr-defined]

    match = resolver.resolve(
        entity_a_id="P-101",
        entity_b_id="P-202",
        complexity=ResolutionComplexity.STANDARD,
    )

    assert match.confidence < 0.70
    assert match.resolution_action in {"review", "separate"}
    assert all(signal.attribute in {"ssn", "taxId", "dob", "name"} for signal in match.match_signals)
