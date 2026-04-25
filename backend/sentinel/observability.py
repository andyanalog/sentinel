import time
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

_MAX_EVENTS = 500


@dataclass
class EvalEvent:
    eval_id: str
    operator_id: str
    action: str
    score: int
    fingerprint: str
    signals: dict[str, float]
    ts: float = field(default_factory=time.time)


class EvalFeed:
    """Thread-safe ring buffer of recent evaluation events. Served to the
    dashboard for live visualization; purely diagnostic — not durable."""

    def __init__(self, capacity: int = _MAX_EVENTS) -> None:
        self._buf: deque[EvalEvent] = deque(maxlen=capacity)
        self._lock = Lock()
        self._seq = 0

    def record(self, event: EvalEvent) -> None:
        with self._lock:
            self._seq += 1
            self._buf.append(event)

    def recent(self, limit: int = 100, since_seq: int | None = None) -> list[EvalEvent]:
        with self._lock:
            items = list(self._buf)
        if since_seq is not None:
            # Best-effort: if the caller knows how many total events it has
            # seen, we return only the tail past that cursor.
            tail = max(0, self._seq - since_seq)
            items = items[-tail:] if tail else []
        return items[-limit:][::-1]

    def counts_by_action(self) -> dict[str, int]:
        out = {"ALLOW": 0, "CHALLENGE": 0, "BLOCK": 0}
        with self._lock:
            for e in self._buf:
                out[e.action] = out.get(e.action, 0) + 1
        return out

    def top_fingerprints(self, limit: int = 10) -> list[dict]:
        with self._lock:
            events = list(self._buf)
        agg: dict[str, dict] = {}
        for e in events:
            row = agg.setdefault(
                e.fingerprint,
                {
                    "fingerprint": e.fingerprint,
                    "hits": 0,
                    "max_score": 0,
                    "last_action": e.action,
                    "operators": set(),
                },
            )
            row["hits"] += 1
            row["max_score"] = max(row["max_score"], e.score)
            row["last_action"] = e.action
            row["operators"].add(e.operator_id)
        ranked = sorted(agg.values(), key=lambda r: (-r["max_score"], -r["hits"]))
        for r in ranked:
            r["operators"] = sorted(r["operators"])
        return ranked[:limit]

    @property
    def total(self) -> int:
        return self._seq

    def timeseries(
        self, window_seconds: int = 300, bucket_seconds: int = 5
    ) -> dict:
        """Bucket events from the last `window_seconds` into fixed-width bins.
        Returns zero-filled series so the frontend chart keeps a stable x-axis
        even during quiet periods.
        """
        now = time.time()
        bucket_seconds = max(1, bucket_seconds)
        n_buckets = max(1, window_seconds // bucket_seconds)

        # Snap bucket edges to absolute-time multiples of `bucket_seconds`.
        # This keeps the x-axis grid stable across polls — labels only
        # advance when we actually cross a bucket boundary, not on every
        # tick. That's the behavior that makes Conviva / Grafana / Datadog
        # live charts feel "calm" instead of sliding continuously.
        last_bucket_start = (int(now) // bucket_seconds) * bucket_seconds
        base = last_bucket_start - (n_buckets - 1) * bucket_seconds
        start = base
        allow = [0] * n_buckets
        challenge = [0] * n_buckets
        block = [0] * n_buckets
        score_sum = [0] * n_buckets
        score_n = [0] * n_buckets

        with self._lock:
            events = list(self._buf)

        for e in events:
            if e.ts < start:
                continue
            idx = int((e.ts - base) // bucket_seconds)
            if idx < 0 or idx >= n_buckets:
                continue
            if e.action == "ALLOW":
                allow[idx] += 1
            elif e.action == "CHALLENGE":
                challenge[idx] += 1
            elif e.action == "BLOCK":
                block[idx] += 1
            score_sum[idx] += e.score
            score_n[idx] += 1

        timestamps = [(base + i * bucket_seconds) for i in range(n_buckets)]
        avg_score = [
            round(score_sum[i] / score_n[i], 1) if score_n[i] else None
            for i in range(n_buckets)
        ]
        return {
            "bucket_seconds": bucket_seconds,
            "window_seconds": window_seconds,
            "timestamps": timestamps,
            # 0..1 — how far through the rightmost (in-progress) bucket we
            # are. The dashboard uses this to visually mark the partial
            # bucket so viewers don't mistake a half-elapsed count for a
            # full one.
            "partial_fraction": round(
                (now - last_bucket_start) / bucket_seconds, 2
            ),
            "allow": allow,
            "challenge": challenge,
            "block": block,
            "avg_score": avg_score,
        }
