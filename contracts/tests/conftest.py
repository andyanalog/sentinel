import pytest


@pytest.fixture
def owner(accounts):
    return accounts[0]


@pytest.fixture
def writer(accounts):
    return accounts[1]


@pytest.fixture
def operator(accounts):
    return accounts[2]


@pytest.fixture
def sentinel_service(accounts):
    return accounts[3]
