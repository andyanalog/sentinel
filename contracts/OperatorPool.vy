# pragma version 0.4.0
# @title Sentinel OperatorPool
# @notice Holds USDC deposits per operator; Sentinel service debits per
#         evaluation call. Operators can withdraw unused balance at any time.

interface IERC20:
    def transferFrom(sender: address, recipient: address, amount: uint256) -> bool: nonpayable
    def transfer(recipient: address, amount: uint256) -> bool: nonpayable

usdc: public(IERC20)
sentinel_service: public(address)
owner: public(address)
balances: public(HashMap[bytes32, uint256])
operator_of: public(HashMap[bytes32, address])

event Deposit:
    operator_id: indexed(bytes32)
    funder: indexed(address)
    amount: uint256

event Debit:
    operator_id: indexed(bytes32)
    amount: uint256
    balance_after: uint256

event Withdraw:
    operator_id: indexed(bytes32)
    to: indexed(address)
    amount: uint256


@deploy
def __init__(usdc_address: address, sentinel_service: address):
    self.owner = msg.sender
    self.usdc = IERC20(usdc_address)
    self.sentinel_service = sentinel_service


@external
def deposit(operator_id: bytes32, amount: uint256):
    assert amount > 0, "zero amount"
    success: bool = extcall self.usdc.transferFrom(msg.sender, self, amount)
    assert success, "transfer failed"
    if self.operator_of[operator_id] == empty(address):
        self.operator_of[operator_id] = msg.sender
    self.balances[operator_id] += amount
    log Deposit(operator_id, msg.sender, amount)


@external
def debit(operator_id: bytes32, amount: uint256):
    assert msg.sender == self.sentinel_service, "only sentinel"
    assert self.balances[operator_id] >= amount, "insufficient pool"
    self.balances[operator_id] -= amount
    log Debit(operator_id, amount, self.balances[operator_id])


@external
def withdraw(operator_id: bytes32, amount: uint256):
    assert msg.sender == self.operator_of[operator_id], "only operator"
    assert self.balances[operator_id] >= amount, "insufficient balance"
    self.balances[operator_id] -= amount
    success: bool = extcall self.usdc.transfer(msg.sender, amount)
    assert success, "transfer failed"
    log Withdraw(operator_id, msg.sender, amount)


@view
@external
def balance_of(operator_id: bytes32) -> uint256:
    return self.balances[operator_id]
