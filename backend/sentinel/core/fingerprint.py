import hashlib

from sentinel.models.evaluation import EvaluationRequest


def _asn_hint(headers: dict[str, str]) -> str:
    for key in ("cf-ipcountry", "x-asn", "x-forwarded-asn"):
        if v := headers.get(key):
            return v
    return ""


def _tls_ja3_hint(headers: dict[str, str]) -> str:
    for key in ("x-ja3", "x-ja3-hash", "cf-tls-fingerprint"):
        if v := headers.get(key):
            return v
    return ""


def extract(req: EvaluationRequest) -> str:
    """Derive a stable, privacy-safe fingerprint from the raw request.

    Hash inputs: ip + asn_hint + tls_ja3 + user_agent. Returns 0x-prefixed
    keccak-style sha256 (32 bytes) so the same value can later round-trip to
    the ReputationLedger contract's bytes32 slot.
    """
    headers_lower = {k.lower(): v for k, v in req.headers.items()}
    parts = [
        req.ip.strip(),
        _asn_hint(headers_lower),
        _tls_ja3_hint(headers_lower),
        req.user_agent.strip(),
    ]
    payload = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return "0x" + digest
