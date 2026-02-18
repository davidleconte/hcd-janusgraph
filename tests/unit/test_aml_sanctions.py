"""
Tests for AML Sanctions Screening module.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from banking.aml.sanctions_screening import (
    SanctionMatch,
    SanctionsScreener,
    ScreeningResult,
)


@pytest.fixture
def mock_deps():
    with (
        patch("banking.aml.sanctions_screening.EmbeddingGenerator") as mock_eg,
        patch("banking.aml.sanctions_screening.VectorSearchClient") as mock_vs,
        patch("banking.aml.sanctions_screening.encode_person_name") as mock_encode,
    ):
        mock_eg_inst = MagicMock()
        mock_eg_inst.dimensions = 384
        mock_eg_inst.encode.return_value = [[0.1] * 384]
        mock_eg.return_value = mock_eg_inst

        mock_vs_inst = MagicMock()
        mock_vs_inst.client.indices.exists.return_value = True
        mock_vs.return_value = mock_vs_inst

        mock_encode.return_value = [0.1] * 384

        yield {
            "eg": mock_eg,
            "eg_inst": mock_eg_inst,
            "vs": mock_vs,
            "vs_inst": mock_vs_inst,
            "encode": mock_encode,
        }


@pytest.fixture
def screener(mock_deps):
    return SanctionsScreener()


class TestDataclasses:
    def test_sanction_match(self):
        match = SanctionMatch(
            customer_name="John",
            sanctioned_name="Jon",
            similarity_score=0.95,
            sanctions_list="OFAC",
            entity_id="E1",
            match_type="fuzzy",
            risk_level="high",
            metadata={},
        )
        assert match.similarity_score == 0.95

    def test_screening_result(self):
        result = ScreeningResult(
            customer_id="C1",
            customer_name="John",
            is_match=False,
            matches=[],
            screening_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.0,
        )
        assert result.is_match is False


class TestSanctionsScreenerInit:
    def test_init(self, mock_deps):
        screener = SanctionsScreener()
        assert screener.index_name == "sanctions_list"

    def test_creates_index_if_not_exists(self, mock_deps):
        mock_deps["vs_inst"].client.indices.exists.return_value = False
        screener = SanctionsScreener()
        mock_deps["vs_inst"].create_vector_index.assert_called_once()


class TestLoadSanctionsList:
    def test_load_sanctions(self, screener, mock_deps):
        mock_deps["eg_inst"].encode.return_value = [[0.1] * 384, [0.2] * 384]
        mock_deps["vs_inst"].bulk_index_documents.return_value = (2, [])

        data = [
            {"name": "Bad Guy", "entity_id": "E1", "sanctions_list": "OFAC"},
            {"name": "Evil Corp", "entity_id": "E2", "entity_type": "company"},
        ]
        count = screener.load_sanctions_list(data)
        assert count == 2

    def test_load_with_errors(self, screener, mock_deps):
        mock_deps["eg_inst"].encode.return_value = [[0.1] * 384]
        mock_deps["vs_inst"].bulk_index_documents.return_value = (0, ["error1"])
        count = screener.load_sanctions_list([{"name": "Test"}])
        assert count == 0


class TestScreenCustomer:
    def test_no_match(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = []
        result = screener.screen_customer("C1", "John Doe")
        assert result.is_match is False
        assert result.confidence == 0.0

    def test_high_risk_match(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = [
            {"score": 0.97, "source": {"name": "John Doe", "list_type": "OFAC", "id": "E1"}},
        ]
        result = screener.screen_customer("C1", "John Doe")
        assert result.is_match is True
        assert result.matches[0].risk_level == "high"

    def test_medium_risk_match(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = [
            {"score": 0.90, "source": {"name": "Jon Doe", "list_type": "UN", "id": "E2"}},
        ]
        result = screener.screen_customer("C1", "John Doe")
        assert result.is_match is True
        assert result.matches[0].risk_level == "medium"

    def test_low_risk_match(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = [
            {"score": 0.78, "source": {"name": "Jane Doe", "list_type": "EU", "id": "E3"}},
        ]
        result = screener.screen_customer("C1", "John Doe")
        assert result.is_match is False
        assert result.matches[0].risk_level == "low"

    def test_exact_match(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = [
            {"score": 0.99, "source": {"name": "John Doe", "list_type": "OFAC", "id": "E1"}},
        ]
        result = screener.screen_customer("C1", "John Doe")
        assert result.matches[0].match_type == "exact"


class TestBatchScreening:
    def test_batch_screen(self, screener, mock_deps):
        mock_deps["vs_inst"].search.return_value = []
        customers = [
            {"customer_id": "C1", "customer_name": "John"},
            {"id": "C2", "name": "Jane"},
        ]
        result = screener.batch_screen_customers(customers)
        assert result["total_screened"] == 2
        assert result["matches_found"] == 0
        assert "processing_time_seconds" in result


class TestGetStatistics:
    def test_get_statistics(self, screener, mock_deps):
        mock_deps["vs_inst"].get_index_stats.return_value = {
            "total": {"docs": {"count": 100}, "store": {"size_in_bytes": 50000}},
        }
        stats = screener.get_statistics()
        assert stats["total_entities"] == 100
        assert stats["index_name"] == "sanctions_list"
