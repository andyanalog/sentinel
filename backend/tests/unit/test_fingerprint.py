from sentinel.core import fingerprint
from sentinel.models.evaluation import EvaluationRequest


def test_fingerprint_is_stable():
    req = EvaluationRequest(ip="1.2.3.4", user_agent="curl/8")
    assert fingerprint.extract(req) == fingerprint.extract(req)


def test_fingerprint_differs_by_ip():
    a = EvaluationRequest(ip="1.2.3.4", user_agent="curl/8")
    b = EvaluationRequest(ip="5.6.7.8", user_agent="curl/8")
    assert fingerprint.extract(a) != fingerprint.extract(b)


def test_fingerprint_is_hex_bytes32():
    fp = fingerprint.extract(EvaluationRequest(ip="1.2.3.4"))
    assert fp.startswith("0x")
    assert len(fp) == 66  # 0x + 64 hex chars
