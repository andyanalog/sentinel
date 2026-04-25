"""Vyper contract tests using Ape (https://apeworx.io).

Run with: `ape test contracts/tests`
"""
import pytest


@pytest.fixture
def ledger(project, owner, writer):
    return owner.deploy(project.ReputationLedger, writer)


def _record(fingerprint: bytes, score: int, reporter, timestamp: int) -> tuple:
    return (fingerprint, score, reporter.address, timestamp)


def test_writer_can_write_batch(ledger, writer, owner):
    fp = b"\x11" * 32
    ledger.write_batch([_record(fp, 80, owner, 1700000000)], sender=writer)
    assert ledger.get_score(fp) == 80


def test_non_writer_cannot_write(ledger, owner, operator):
    fp = b"\x22" * 32
    with pytest.raises(Exception):
        ledger.write_batch([_record(fp, 50, owner, 1700000000)], sender=operator)


def test_merge_is_ema(ledger, writer, owner):
    fp = b"\x33" * 32
    ledger.write_batch([_record(fp, 100, owner, 1)], sender=writer)
    ledger.write_batch([_record(fp, 0, owner, 2)], sender=writer)
    # 70% of 100 + 30% of 0 = 70
    assert ledger.get_score(fp) == 70


def test_owner_can_rotate_writer(ledger, owner, writer, accounts):
    new_writer = accounts[4]
    ledger.set_writer(new_writer, sender=owner)
    assert ledger.writer() == new_writer.address
