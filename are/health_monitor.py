"""
AHFMES ARE — Local System Health Monitor & Watchdog (DELEGASI_033, Autonomic Nervous System)

Continuously evaluates infrastructure health (Memory, MT5 Heartbeat, Network Latency, Vault Integrity).
Triggers Circuit Breaker veto via CapitalSafetyKernel when CRITICAL anomalies occur.
100% Python Standard Library.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, List, Optional, Tuple


class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class HealthReport:
    status: HealthStatus
    memory_mb: float
    heartbeat_ok: bool
    latency_ok: bool
    vault_ok: bool
    details: str


def _get_process_memory_mb() -> float:
    """Retrieves current process working set RAM in megabytes (Windows + cross-platform fallback)."""
    try:
        if sys.platform == "win32":
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            GetProcessMemoryInfo = ctypes.windll.psapi.GetProcessMemoryInfo
            GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
            GetProcessMemoryInfo.restype = wintypes.BOOL

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return float(counters.WorkingSetSize) / (1024.0 * 1024.0)
    except Exception:
        pass

    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # On Linux ru_maxrss is in KB, on macOS in bytes
        if sys.platform == "darwin":
            return float(rusage.ru_maxrss) / (1024.0 * 1024.0)
        return float(rusage.ru_maxrss) / 1024.0
    except Exception:
        pass

    return 50.0


class SystemHealthMonitor:
    """
    Local Watchdog monitoring core execution and infrastructure vitals.
    """

    def check_memory_usage(self, threshold_mb: float = 2048.0) -> Tuple[bool, float]:
        """
        Checks process RAM usage against specified threshold in MB.
        """
        current_mb = _get_process_memory_mb()
        is_healthy = current_mb <= threshold_mb
        return is_healthy, current_mb

    def check_mt5_heartbeat(
        self,
        last_tick_timestamp: float,
        max_silence_seconds: float = 10.0,
        current_time: Optional[float] = None,
    ) -> bool:
        """
        Validates whether MT5 feed has provided ticks recently.
        """
        if last_tick_timestamp <= 0:
            return False
        now = time.time() if current_time is None else current_time
        silence = now - last_tick_timestamp
        return silence <= max_silence_seconds

    def check_latency_spike(
        self,
        recent_latencies: List[float],
        max_avg_latency_ms: float = 2000.0,
    ) -> bool:
        """
        Validates execution latency against maximum average and single-tick spike thresholds.
        """
        if not recent_latencies:
            return True

        # Extreme single-tick latency spike (> 5000ms)
        if any(lat > 5000.0 for lat in recent_latencies):
            return False

        avg_latency = sum(recent_latencies) / len(recent_latencies)
        return avg_latency <= max_avg_latency_ms

    def check_vault_integrity(self, event_store: Optional[Any] = None) -> bool:
        """
        Verifies dual-layer cryptographic integrity of the local Vault.
        """
        if event_store is None:
            return True

        if hasattr(event_store, "verify_full_chain_integrity"):
            try:
                ok, status = event_store.verify_full_chain_integrity()
                return bool(ok and status == "OK")
            except Exception:
                return False

        return True

    def evaluate_system_health(
        self,
        last_tick_ts: float,
        latencies: List[float],
        event_store: Optional[Any] = None,
        memory_limit_mb: float = 2048.0,
        current_time: Optional[float] = None,
    ) -> HealthReport:
        """
        Executes full health check battery and categorizes operational state.
        """
        mem_ok, current_mb = self.check_memory_usage(threshold_mb=memory_limit_mb)
        heartbeat_ok = self.check_mt5_heartbeat(last_tick_ts, max_silence_seconds=10.0, current_time=current_time)
        latency_ok = self.check_latency_spike(latencies, max_avg_latency_ms=2000.0)
        vault_ok = self.check_vault_integrity(event_store)

        # 1. Evaluate Critical Failures
        critical_reasons: List[str] = []
        if not heartbeat_ok:
            critical_reasons.append("MT5 Heartbeat Silence (>10s)")
        if not latency_ok:
            critical_reasons.append("Extreme Latency Spike (>5000ms or avg >2000ms)")
        if not mem_ok:
            critical_reasons.append(f"Memory Limit Exceeded ({current_mb:.1f}MB > {memory_limit_mb:.1f}MB)")
        if not vault_ok:
            critical_reasons.append("Vault Integrity Mismatch / Corruption Detected")

        if critical_reasons:
            return HealthReport(
                status=HealthStatus.CRITICAL,
                memory_mb=round(current_mb, 2),
                heartbeat_ok=heartbeat_ok,
                latency_ok=latency_ok,
                vault_ok=vault_ok,
                details="; ".join(critical_reasons),
            )

        # 2. Evaluate Warnings
        warning_reasons: List[str] = []
        if latencies:
            avg_lat = sum(latencies) / len(latencies)
            if 1000.0 <= avg_lat <= 2000.0:
                warning_reasons.append(f"Elevated Average Latency ({avg_lat:.1f}ms)")
        if current_mb >= (0.8 * memory_limit_mb):
            warning_reasons.append(f"Elevated Memory Footprint ({current_mb:.1f}MB)")

        if warning_reasons:
            return HealthReport(
                status=HealthStatus.WARNING,
                memory_mb=round(current_mb, 2),
                heartbeat_ok=heartbeat_ok,
                latency_ok=latency_ok,
                vault_ok=vault_ok,
                details="; ".join(warning_reasons),
            )

        # 3. All Nominal
        return HealthReport(
            status=HealthStatus.HEALTHY,
            memory_mb=round(current_mb, 2),
            heartbeat_ok=True,
            latency_ok=True,
            vault_ok=True,
            details="System nominal",
        )