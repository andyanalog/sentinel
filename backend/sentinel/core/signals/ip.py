import ipaddress

from sentinel.core.signals.base import BaseSignal, SignalContext
from sentinel.models.evaluation import EvaluationRequest, SignalResult

# Small curated list of ranges historically associated with hosting/VPS
# providers. Not exhaustive — a real deployment would back this with an ASN
# database (MaxMind, IPinfo).
_SUSPICIOUS_PREFIXES = [
    "5.188.0.0/16",      # commonly abused hosting
    "45.95.0.0/16",
    "185.220.0.0/16",    # tor exits
    "104.131.0.0/16",    # digitalocean
    "167.99.0.0/16",     # digitalocean
    "172.104.0.0/16",    # linode
]


class IpAsnSignal(BaseSignal):
    name = "ip_asn"
    weight = 0.6

    def __init__(self) -> None:
        self._networks = [
            ipaddress.ip_network(p, strict=False) for p in _SUSPICIOUS_PREFIXES
        ]

    async def evaluate(
        self, req: EvaluationRequest, ctx: SignalContext
    ) -> SignalResult:
        value = 0.0
        try:
            addr = ipaddress.ip_address(req.ip)
            if addr.is_private or addr.is_loopback:
                value = 0.0
            else:
                for net in self._networks:
                    if addr in net:
                        value = 0.7
                        break
        except ValueError:
            value = 0.3
        return SignalResult(name=self.name, value=value, weight=self.weight)
