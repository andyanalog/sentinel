# pragma version 0.4.0
# @title Sentinel ReputationLedger
# @notice Stores hashed request fingerprints and severity scores written in
#         batches by the Sentinel backend. Any contract or dapp on Arc can
#         read from `get_score` / `get_record` for cross-app trust lookups.
# @dev Only the designated `writer` (the Sentinel operator EOA / contract)
#      can call `write_batch`.

struct Record:
    fingerprint: bytes32
    score: uint8
    reported_by: address
    timestamp: uint256

writer: public(address)
owner: public(address)
records: public(HashMap[bytes32, Record])

event ScoreWritten:
    fingerprint: indexed(bytes32)
    score: uint8
    reported_by: indexed(address)
    timestamp: uint256

event WriterUpdated:
    old_writer: indexed(address)
    new_writer: indexed(address)


@deploy
def __init__(initial_writer: address):
    self.owner = msg.sender
    self.writer = initial_writer


@external
def set_writer(new_writer: address):
    assert msg.sender == self.owner, "only owner"
    log WriterUpdated(self.writer, new_writer)
    self.writer = new_writer


@external
def write_batch(batch: DynArray[Record, 100]):
    assert msg.sender == self.writer, "only writer"
    for r: Record in batch:
        existing: Record = self.records[r.fingerprint]
        # EMA-style merge: 70% prior, 30% new, so a single noisy write can't
        # poison the slot but repeat bad behavior escalates quickly.
        merged_score: uint8 = r.score
        if existing.timestamp != 0:
            merged_score = convert(
                (convert(existing.score, uint256) * 7
                 + convert(r.score, uint256) * 3) // 10,
                uint8,
            )
        self.records[r.fingerprint] = Record(
            fingerprint=r.fingerprint,
            score=merged_score,
            reported_by=r.reported_by,
            timestamp=r.timestamp,
        )
        log ScoreWritten(r.fingerprint, merged_score, r.reported_by, r.timestamp)


@view
@external
def get_score(fingerprint: bytes32) -> uint8:
    return self.records[fingerprint].score


@view
@external
def get_record(fingerprint: bytes32) -> Record:
    return self.records[fingerprint]
