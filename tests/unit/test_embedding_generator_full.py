"""Comprehensive tests for src.python.utils.embedding_generator — targets 29% → 90%+."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class FakeSentenceTransformer:
    def __init__(self, *a, **kw):
        pass

    def encode(
        self,
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    ):
        n = len(texts) if isinstance(texts, list) else 1
        return np.random.rand(n, 384).astype(np.float32)


@pytest.fixture(autouse=True)
def mock_sentence_transformer():
    with (
        patch("src.python.utils.embedding_generator.SentenceTransformer", FakeSentenceTransformer),
        patch("src.python.utils.embedding_generator._HAS_ML_DEPS", True),
    ):
        yield


from src.python.utils.embedding_generator import (
    EmbeddingGenerator,
    encode_person_name,
    encode_transaction_description,
    encode_sanctions_list,
)


class TestEmbeddingGenerator:
    def test_init_mini(self):
        gen = EmbeddingGenerator(model_name="mini")
        assert gen.dimensions == 384
        assert gen.model_name == "mini"

    def test_init_mpnet(self):
        gen = EmbeddingGenerator(model_name="mpnet")
        assert gen.dimensions == 768

    def test_init_invalid(self):
        with pytest.raises(ValueError, match="Unknown model"):
            EmbeddingGenerator(model_name="bad")

    def test_encode_single_string(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = gen.encode("hello")
        assert result.shape[0] == 1

    def test_encode_list(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = gen.encode(["a", "b", "c"])
        assert result.shape[0] == 3

    def test_encode_for_search(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = gen.encode_for_search("query")
        assert result.ndim == 1

    def test_encode_batch(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = gen.encode_batch(["a", "b"])
        assert len(result) == 2
        assert isinstance(result[0], np.ndarray)

    def test_similarity(self):
        gen = EmbeddingGenerator(model_name="mini")
        e1 = np.random.rand(384).astype(np.float32)
        e2 = np.random.rand(384).astype(np.float32)
        sim = gen.similarity(e1, e2)
        assert -1.0 <= sim <= 1.0

    def test_batch_similarity(self):
        gen = EmbeddingGenerator(model_name="mini")
        query = np.random.rand(384).astype(np.float32)
        candidates = np.random.rand(5, 384).astype(np.float32)
        sims = gen.batch_similarity(query, candidates)
        assert sims.shape == (5,)


class TestHelperFunctions:
    def test_encode_person_name(self):
        result = encode_person_name("John Smith")
        assert result.ndim == 1

    def test_encode_person_name_with_generator(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = encode_person_name("John Smith", generator=gen)
        assert result.ndim == 1

    def test_encode_transaction_description(self):
        result = encode_transaction_description("Wire transfer to offshore")
        assert result.ndim == 1

    def test_encode_transaction_description_with_generator(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = encode_transaction_description("Payment", generator=gen)
        assert result.ndim == 1

    def test_encode_sanctions_list(self):
        result = encode_sanctions_list(["Name One", "Name Two"])
        assert result.shape[0] == 2

    def test_encode_sanctions_list_with_generator(self):
        gen = EmbeddingGenerator(model_name="mini")
        result = encode_sanctions_list(["A", "B"], generator=gen)
        assert result.shape[0] == 2
