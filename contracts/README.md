# Sentinel Contracts

Two Vyper 0.4 contracts on Arc L1.

- `ReputationLedger.vy` — shared hashed-fingerprint → score store (cross-app)
- `OperatorPool.vy` — USDC deposits per operator, debited per evaluation

## Toolchain

Uses [ApeWorX](https://apeworx.io) (`pip install eth-ape 'ape-vyper>=0.8'`).

```bash
ape compile
ape test contracts/tests

# Deploy
export SENTINEL_WRITER_ADDRESS=0x...
export USDC_ADDRESS=0x...
export SENTINEL_SERVICE_ADDRESS=0x...
ape run contracts/deploy/deploy.py --network arc:testnet
```
