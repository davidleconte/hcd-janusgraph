"""Tests for banking.data_generators.events modules."""

from datetime import date, datetime, timedelta

import pytest

from banking.data_generators.events.communication_generator import CommunicationGenerator
from banking.data_generators.events.trade_generator import TradeGenerator
from banking.data_generators.events.transaction_generator import TransactionGenerator
from banking.data_generators.utils.data_models import (
    Communication,
    Trade,
    Transaction,
)


class TestTransactionGenerator:
    def test_generate(self):
        gen = TransactionGenerator(seed=42)
        tx = gen.generate(from_account_id="a-1", to_account_id="a-2")
        assert isinstance(tx, Transaction)
        assert tx.from_account_id == "a-1"
        assert tx.to_account_id == "a-2"
        assert tx.amount > 0
        assert tx.currency

    def test_generate_batch(self):
        gen = TransactionGenerator(seed=42)
        txs = gen.generate_batch(5)
        assert len(txs) == 5

    def test_generate_with_config(self):
        gen = TransactionGenerator(seed=42, config={"min_amount": 100, "max_amount": 200})
        tx = gen.generate(from_account_id="a-1", to_account_id="a-2")
        assert tx.amount >= 100


class TestCommunicationGenerator:
    def test_generate(self):
        gen = CommunicationGenerator(seed=42)
        comm = gen.generate(sender_id="p-1", recipient_id="p-2")
        assert isinstance(comm, Communication)

    def test_generate_batch(self):
        gen = CommunicationGenerator(seed=42)
        comms = gen.generate_batch(5)
        assert len(comms) == 5


class TestTradeGenerator:
    def test_generate(self):
        gen = TradeGenerator(seed=42)
        trade = gen.generate(trader_id="p-1", account_id="a-1")
        assert isinstance(trade, Trade)

    def test_generate_batch(self):
        gen = TradeGenerator(seed=42)
        trades = gen.generate_batch(5)
        assert len(trades) == 5
