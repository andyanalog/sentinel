# pragma version 0.4.0
# @title MockERC20
# @notice Minimal ERC20-shaped mock for OperatorPool tests. Not for deployment.

balances: public(HashMap[address, uint256])


@external
def mint(to: address, amount: uint256):
    self.balances[to] += amount


@external
def approve(_spender: address, _amount: uint256) -> bool:
    return True


@external
def transferFrom(sender: address, recipient: address, amount: uint256) -> bool:
    assert self.balances[sender] >= amount, "insufficient"
    self.balances[sender] -= amount
    self.balances[recipient] += amount
    return True


@external
def transfer(recipient: address, amount: uint256) -> bool:
    assert self.balances[msg.sender] >= amount, "insufficient"
    self.balances[msg.sender] -= amount
    self.balances[recipient] += amount
    return True
