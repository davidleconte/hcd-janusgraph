"""
Tests for AML Sanctions Screening Module

Tests cover:
- SanctionMatch and ScreeningResult dataclasses
- SanctionsScreener initialization
- Index management
- Sanctions list loading
- Customer screening (single and batch)
- Risk level determination
- Statistics retrieval
"""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from banking.aml.sanctions_screening import (
    SanctionMatch,
    SanctionsScreener,
    ScreeningResult,
)

# ============================================================================
# Test Dataclasses
# ============================================================================


class TestSanctionMatch:
    """Test SanctionMatch dataclass."""

    def test_match_creation(self):
        """Test creating a sanction match."""
        match = SanctionMatch(
            customer_name="John Smith",
            sanctioned_name="John Smyth",
            similarity_score=0.92,
            sanctions_list="OFAC",
            entity_id="SANC-123",
            match_type="fuzzy",
            risk_level="high",
            metadata={"country": "US", "entity_type": "person"},
        )

        assert match.customer_name == "John Smith"
        assert match.sanctioned_name == "John Smyth"
        assert match.similarity_score == 0.92
        assert match.sanctions_list == "OFAC"
        assert match.match_type == "fuzzy"
        assert match.risk_level == "high"

    def test_match_types(self):
        """Test different match types."""
        match_types = ["exact", "fuzzy", "phonetic"]
        for mtype in match_types:
            match = SanctionMatch(
                customer_name="Test Name",
                sanctioned_name="Test Name",
                similarity_score=0.95,
                sanctions_list="UN",
                entity_id="TEST-123",
                match_type=mtype,
                risk_level="high",
                metadata={},
            )
            assert match.match_type == mtype

    def test_risk_levels(self):
        """Test different risk levels."""
        risk_levels = ["high", "medium", "low"]
        for level in risk_levels:
            match = SanctionMatch(
                customer_name="Test Name",
                sanctioned_name="Test Name",
                similarity_score=0.85,
                sanctions_list="EU",
                entity_id="TEST-123",
                match_type="fuzzy",
                risk_level=level,
                metadata={},
            )
            assert match.risk_level == level


class TestScreeningResult:
    """Test ScreeningResult dataclass."""

    def test_result_creation_with_match(self):
        """Test creating a screening result with matches."""
        match = SanctionMatch(
            customer_name="John Smith",
            sanctioned_name="John Smyth",
            similarity_score=0.92,
            sanctions_list="OFAC",
            entity_id="SANC-123",
            match_type="fuzzy",
            risk_level="high",
            metadata={},
        )

        result = ScreeningResult(
            customer_id="CUST-456",
            customer_name="John Smith",
            is_match=True,
            matches=[match],
            screening_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.92,
        )

        assert result.customer_id == "CUST-456"
        assert result.is_match is True
        assert len(result.matches) == 1
        assert result.confidence == 0.92

    def test_result_creation_no_match(self):
        """Test creating a screening result with no matches."""
        result = ScreeningResult(
            customer_id="CUST-789",
            customer_name="Jane Doe",
            is_match=False,
            matches=[],
            screening_timestamp=datetime.now(timezone.utc).isoformat(),
            confidence=0.0,
        )

        assert result.is_match is False
        assert len(result.matches) == 0
        assert result.confidence == 0.0


# ============================================================================
# Test SanctionsScreener Initialization
# ============================================================================


class TestSanctionsScreenerInit:
    """Test SanctionsScreener initialization."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_default_initialization(self, mock_generator, mock_search_client):
        """Test screener with default parameters."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance

        screener = SanctionsScreener()

        assert screener.index_name == "sanctions_list"
        mock_generator.assert_called_once_with(model_name="mini")
        mock_search_client.assert_called_once_with(host="localhost", port=9200)

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_custom_parameters(self, mock_generator, mock_search_client):
        """Test screener with custom parameters."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 768
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance

        screener = SanctionsScreener(
            opensearch_host="search.example.com",
            opensearch_port=9300,
            embedding_model="mpnet",
            index_name="custom_sanctions",
        )

        assert screener.index_name == "custom_sanctions"
        mock_generator.assert_called_once_with(model_name="mpnet")
        mock_search_client.assert_called_once_with(host="search.example.com", port=9300)

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_class_constants(self, mock_generator, mock_search_client):
        """Test class-level risk thresholds."""
        assert SanctionsScreener.HIGH_RISK_THRESHOLD == 0.95
        assert SanctionsScreener.MEDIUM_RISK_THRESHOLD == 0.85
        assert SanctionsScreener.LOW_RISK_THRESHOLD == 0.75


# ============================================================================
# Test Index Management
# ============================================================================


class TestIndexManagement:
    """Test index creation and management."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_ensure_index_exists_creates_index(self, mock_generator, mock_search_client):
        """Test index creation when it doesn't exist."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = False
        mock_search_client.return_value = mock_client_instance

        SanctionsScreener()

        mock_client_instance.create_vector_index.assert_called_once()
        call_args = mock_client_instance.create_vector_index.call_args
        assert call_args[1]["index_name"] == "sanctions_list"
        assert call_args[1]["vector_dimension"] == 384

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_ensure_index_exists_skips_existing(self, mock_generator, mock_search_client):
        """Test index creation is skipped when index exists."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_search_client.return_value = mock_client_instance

        SanctionsScreener()

        mock_client_instance.create_vector_index.assert_not_called()


# ============================================================================
# Test Sanctions List Loading
# ============================================================================


class TestSanctionsListLoading:
    """Test loading sanctions lists."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_load_sanctions_list(self, mock_generator, mock_search_client):
        """Test loading sanctions list."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_gen_instance.encode.return_value = [[0.1] * 384, [0.2] * 384]
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.bulk_index_documents.return_value = (2, [])
        mock_search_client.return_value = mock_client_instance

        screener = SanctionsScreener()

        sanctions_data = [
            {
                "name": "John Doe",
                "entity_id": "SANC-001",
                "sanctions_list": "OFAC",
                "entity_type": "person",
                "country": "US",
            },
            {
                "name": "Jane Smith",
                "entity_id": "SANC-002",
                "sanctions_list": "UN",
                "entity_type": "person",
                "country": "UK",
            },
        ]

        count = screener.load_sanctions_list(sanctions_data)

        assert count == 2
        mock_gen_instance.encode.assert_called_once()
        mock_client_instance.bulk_index_documents.assert_called_once()

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_load_sanctions_list_with_errors(self, mock_generator, mock_search_client):
        """Test loading sanctions list with indexing errors."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_gen_instance.encode.return_value = [[0.1] * 384]
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.bulk_index_documents.return_value = (0, ["Error 1"])
        mock_search_client.return_value = mock_client_instance

        screener = SanctionsScreener()

        sanctions_data = [{"name": "John Doe", "entity_id": "SANC-001"}]

        count = screener.load_sanctions_list(sanctions_data)

        assert count == 0


# ============================================================================
# Test Customer Screening
# ============================================================================


class TestCustomerScreening:
    """Test customer screening functionality."""

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_no_match(self, mock_generator, mock_search_client, mock_encode):
        """Test screening customer with no matches."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = []
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-123", "John Doe")

        assert result.customer_id == "CUST-123"
        assert result.customer_name == "John Doe"
        assert result.is_match is False
        assert len(result.matches) == 0
        assert result.confidence == 0.0

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_high_risk_match(self, mock_generator, mock_search_client, mock_encode):
        """Test screening customer with high-risk match."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = [
            {
                "score": 0.96,
                "source": {
                    "name": "John Doe",
                    "id": "SANC-001",
                    "list_type": "OFAC",
                    "entity_type": "person",
                    "country": "US",
                },
            }
        ]
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-123", "John Doe")

        assert result.is_match is True
        assert len(result.matches) == 1
        assert result.matches[0].risk_level == "high"
        assert result.matches[0].match_type == "fuzzy"
        assert result.confidence == 0.96

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_exact_match(self, mock_generator, mock_search_client, mock_encode):
        """Test screening customer with exact match."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = [
            {
                "score": 0.99,
                "source": {
                    "name": "John Doe",
                    "id": "SANC-001",
                    "list_type": "OFAC",
                },
            }
        ]
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-123", "John Doe")

        assert result.matches[0].match_type == "exact"
        assert result.matches[0].risk_level == "high"

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_medium_risk_match(
        self, mock_generator, mock_search_client, mock_encode
    ):
        """Test screening customer with medium-risk match."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = [
            {
                "score": 0.88,
                "source": {
                    "name": "John Smyth",
                    "id": "SANC-001",
                    "list_type": "UN",
                },
            }
        ]
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-123", "John Smith")

        assert result.is_match is True
        assert result.matches[0].risk_level == "medium"
        assert result.matches[0].match_type == "fuzzy"

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_screen_customer_low_risk_match(self, mock_generator, mock_search_client, mock_encode):
        """Test screening customer with low-risk match."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = [
            {
                "score": 0.78,
                "source": {
                    "name": "Jon Doe",
                    "id": "SANC-001",
                    "list_type": "EU",
                },
            }
        ]
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()
        result = screener.screen_customer("CUST-123", "John Doe")

        assert result.is_match is False  # Below medium threshold
        assert len(result.matches) == 1
        assert result.matches[0].risk_level == "low"
        assert result.matches[0].match_type == "phonetic"


# ============================================================================
# Test Batch Screening
# ============================================================================


class TestBatchScreening:
    """Test batch customer screening."""

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_batch_screen_customers(self, mock_generator, mock_search_client, mock_encode):
        """Test batch screening multiple customers."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = []
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()

        customers = [
            {"customer_id": "CUST-1", "customer_name": "John Doe"},
            {"customer_id": "CUST-2", "customer_name": "Jane Smith"},
            {"customer_id": "CUST-3", "customer_name": "Bob Johnson"},
        ]

        result = screener.batch_screen_customers(customers)

        assert result["total_screened"] == 3
        assert result["matches_found"] == 0
        assert "processing_time_seconds" in result
        assert len(result["results"]) == 3

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_batch_screen_with_matches(self, mock_generator, mock_search_client, mock_encode):
        """Test batch screening with some matches."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True

        # First customer: match, second: no match
        mock_client_instance.search.side_effect = [
            [
                {
                    "score": 0.96,
                    "source": {"name": "John Doe", "id": "SANC-001", "list_type": "OFAC"},
                }
            ],
            [],
        ]
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()

        customers = [
            {"customer_id": "CUST-1", "customer_name": "John Doe"},
            {"customer_id": "CUST-2", "customer_name": "Jane Smith"},
        ]

        result = screener.batch_screen_customers(customers)

        assert result["total_screened"] == 2
        assert result["matches_found"] == 1

    @patch("banking.aml.sanctions_screening.encode_person_name")
    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_batch_screen_alternative_keys(self, mock_generator, mock_search_client, mock_encode):
        """Test batch screening with alternative key names (id/name)."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.search.return_value = []
        mock_search_client.return_value = mock_client_instance

        mock_encode.return_value = [0.1] * 384

        screener = SanctionsScreener()

        # Using 'id' and 'name' instead of 'customer_id' and 'customer_name'
        customers = [
            {"id": "CUST-1", "name": "John Doe"},
            {"id": "CUST-2", "name": "Jane Smith"},
        ]

        result = screener.batch_screen_customers(customers)

        assert result["total_screened"] == 2
        assert len(result["results"]) == 2


# ============================================================================
# Test Statistics
# ============================================================================


class TestStatistics:
    """Test statistics retrieval."""

    @patch("banking.aml.sanctions_screening.VectorSearchClient")
    @patch("banking.aml.sanctions_screening.EmbeddingGenerator")
    def test_get_statistics(self, mock_generator, mock_search_client):
        """Test getting sanctions list statistics."""
        mock_gen_instance = Mock()
        mock_gen_instance.dimensions = 384
        mock_generator.return_value = mock_gen_instance

        mock_client_instance = Mock()
        mock_client_instance.client.indices.exists.return_value = True
        mock_client_instance.get_index_stats.return_value = {
            "total": {"docs": {"count": 1000}, "store": {"size_in_bytes": 5000000}}
        }
        mock_search_client.return_value = mock_client_instance

        screener = SanctionsScreener()
        stats = screener.get_statistics()

        assert stats["total_entities"] == 1000
        assert stats["index_size_bytes"] == 5000000
        assert stats["index_name"] == "sanctions_list"
        assert stats["embedding_dimensions"] == 384


# Made with Bob
