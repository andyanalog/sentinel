"""Vyper contract tests for OperatorPool using a MockERC20 stand-in for USDC."""
import pytest


@pytest.fixture
def usdc(owner, project):
    return owner.deploy(project.MockERC20)


@pytest.fixture
def pool(owner, project, sentinel_service, usdc):
    return owner.deploy(project.OperatorPool, usdc.address, sentinel_service)


def test_deposit_credits_balance(pool, operator, usdc):
    op_id = b"\xaa" * 32
    usdc.mint(operator, 1000, sender=operator)
    usdc.approve(pool.address, 1000, sender=operator)
    pool.deposit(op_id, 500, sender=operator)
    assert pool.balance_of(op_id) == 500


def test_debit_only_by_sentinel_service(pool, operator, sentinel_service, usdc):
    op_id = b"\xbb" * 32
    usdc.mint(operator, 1000, sender=operator)
    usdc.approve(pool.address, 1000, sender=operator)
    pool.deposit(op_id, 300, sender=operator)

    # Non-service caller is rejected.
    with pytest.raises(Exception):
        pool.debit(op_id, 1, sender=operator)

    # Service can debit and balance drops.
    pool.debit(op_id, 100, sender=sentinel_service)
    assert pool.balance_of(op_id) == 200


def test_debit_rejects_overdraft(pool, operator, sentinel_service, usdc):
    op_id = b"\xcc" * 32
    usdc.mint(operator, 1000, sender=operator)
    usdc.approve(pool.address, 1000, sender=operator)
    pool.deposit(op_id, 50, sender=operator)
    with pytest.raises(Exception):
        pool.debit(op_id, 51, sender=sentinel_service)


def test_withdraw_only_by_depositor(pool, operator, accounts, usdc):
    op_id = b"\xdd" * 32
    usdc.mint(operator, 1000, sender=operator)
    usdc.approve(pool.address, 1000, sender=operator)
    pool.deposit(op_id, 400, sender=operator)

    intruder = accounts[5]
    with pytest.raises(Exception):
        pool.withdraw(op_id, 100, sender=intruder)

    pool.withdraw(op_id, 100, sender=operator)
    assert pool.balance_of(op_id) == 300
