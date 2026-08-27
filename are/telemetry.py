"""
AHFMES ARE-3 — Telemetry Aggregator (Slice-2 Part C)

Implements:
- ExperimentTrace: structured, content-addressed telemetry event.
- TelemetryAggregator: records research traces to EventStore stream "research_telemetry" (ACC-313),
  retrieves candidate trace histories, and computes deterministic statistical aggregates (ACC-314).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from are.storage import EventStore


@dataclass(frozen=True)
class ExperimentTrace:
    experiment_id: str
    candidate_id: str
    timestamp: float
    metrics: Dict[str, float]
    tags: List[str]
    trace_hash: str = ""

    def __post_init__(self):
        if not self.trace_hash:
            canonical_repr = {
                "experiment_id": self.experiment_id,
                "candidate_id": self.candidate_id,
                "timestamp": self.timestamp,
                "metrics": self.metrics,
                "tags": sorted(self.tags),
            }
            raw = json.dumps(canonical_repr, sort_keys=True).encode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            object.__setattr__(self, "trace_hash", digest)


class TelemetryAggregator:
    """
    Manages telemetry traces for candidate models and experiments in EventStore.
    """

    STREAM_ID = "research_telemetry"

    def __init__(self, event_store: EventStore):
        self.event_store = event_store

    def record_trace(self, trace: ExperimentTrace) -> str:
        """
        Appends an ExperimentTrace into the EventStore research_telemetry stream (ACC-313).
        Returns the committed event hash.
        """
        payload = {
            "experiment_id": trace.experiment_id,
            "candidate_id": trace.candidate_id,
            "timestamp": trace.timestamp,
            "metrics": trace.metrics,
            "tags": trace.tags,
            "trace_hash": trace.trace_hash,
        }
        event_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")

        head = self.event_store.get_head(self.STREAM_ID)
        if head is None:
            expected_rev = 0
            prev_hash = "0" * 64
        else:
            expected_rev = head[0]
            prev_hash = head[1]

        rec = self.event_store.append_event(
            stream_id=self.STREAM_ID,
            event_data=event_bytes,
            expected_revision=expected_rev,
            prev_event_hash=prev_hash,
        )
        return rec.event_hash

    def get_experiment_traces(self, candidate_id: str) -> List[ExperimentTrace]:
        """
        Retrieves all committed traces for the given candidate_id.
        """
        head = self.event_store.get_head(self.STREAM_ID)
        if head is None:
            return []

        traces: List[ExperimentTrace] = []
        for rev in range(1, head[0] + 1):
            ev = self.event_store.get_event(self.STREAM_ID, rev)
            if ev is not None:
                data = json.loads(ev.event_data.decode("utf-8"))
                if data.get("candidate_id") == candidate_id:
                    traces.append(
                        ExperimentTrace(
                            experiment_id=data["experiment_id"],
                            candidate_id=data["candidate_id"],
                            timestamp=float(data["timestamp"]),
                            metrics=data.get("metrics", {}),
                            tags=data.get("tags", []),
                            trace_hash=data.get("trace_hash", ""),
                        )
                    )
        return traces

    def compute_aggregate_metrics(self, candidate_id: str) -> Dict[str, float]:
        """
        Computes deterministic metrics across all candidate traces (ACC-314).
        Calculates mean, p50 (median), p95, and stability_index.
        """
        traces = self.get_experiment_traces(candidate_id)
        if not traces:
            return {}

        # Collect all metric keys
        metric_values: Dict[str, List[float]] = {}
        for tr in traces:
            for k, v in tr.metrics.items():
                metric_values.setdefault(k, []).append(float(v))

        aggregates: Dict[str, float] = {
            "trace_count": float(len(traces)),
        }

        for key, values in metric_values.items():
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            mean_val = sum(sorted_vals) / n

            # P50 (Median)
            if n % 2 == 1:
                p50 = sorted_vals[n // 2]
            else:
                p50 = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0

            # P95 (Nearest-rank / interpolated percentile)
            idx_95 = min(n - 1, int(math.ceil(0.95 * n)) - 1)
            p95 = sorted_vals[max(0, idx_95)]

            # Variance and Stability Index: 1 / (1 + variance)
            variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n
            stability = 1.0 / (1.0 + variance)

            aggregates[f"{key}_mean"] = round(mean_val, 6)
            aggregates[f"{key}_p50"] = round(p50, 6)
            aggregates[f"{key}_p95"] = round(p95, 6)
            aggregates[f"{key}_variance"] = round(variance, 6)
            aggregates[f"{key}_stability_index"] = round(stability, 6)

        return aggregates
