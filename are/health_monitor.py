"""
AHFMES ARE — Local System Health Monitor & Watchdog (DELEGASI_033, Autonomic Nervous System)

Continuously evaluates infrastructure health (Memory, MT5 Heartbeat, Network Latency, Vault Integrity).
Triggers Circuit Breaker veto via CapitalSafetyKernel when CRITICAL anomalies occur.
100% Python Standard Library.
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
import time
import urllib.request
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


class CriticalAlertSender:
    """
    External Alerting Gateway for CRITICAL health events (DELEGASI_035B).
    Supports Webhook (primary) and SMTP Email (fallback) with 5-minute rate limiting.
    100% Python Standard Library.
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        email_smtp_host: Optional[str] = None,
        email_from: Optional[str] = None,
        email_to: Optional[str] = None,
        rate_limit_seconds: float = 300.0,
        email_smtp_port: int = 587,
        email_user: Optional[str] = None,
        email_password: Optional[str] = None,
    ):
        self.webhook_url = webhook_url
        self.email_smtp_host = email_smtp_host
        self.email_from = email_from
        self.email_to = email_to
        self.rate_limit_seconds = float(rate_limit_seconds)
        self.email_smtp_port = int(email_smtp_port)
        self.email_user = email_user
        self.email_password = email_password
        self._last_alert_ts: float = 0.0

    def send_alert(
        self,
        health_report: HealthReport,
        champion_id: str = "NONE",
        evidence_hash: str = "",
        current_time: Optional[float] = None,
    ) -> bool:
        """
        Sends an alert if status is CRITICAL and rate limit has expired.
        Tries Webhook first, then falls back to Email SMTP.
        """
        if health_report.status != HealthStatus.CRITICAL:
            return False

        now = time.time() if current_time is None else current_time
        if (now - self._last_alert_ts) < self.rate_limit_seconds:
            return False

        payload = {
            "alert_type": "CRITICAL_HEALTH_ALERT",
            "status": health_report.status.value,
            "champion_id": champion_id,
            "evidence_hash": evidence_hash,
            "details": health_report.details,
            "memory_mb": health_report.memory_mb,
            "heartbeat_ok": health_report.heartbeat_ok,
            "latency_ok": health_report.latency_ok,
            "vault_ok": health_report.vault_ok,
            "timestamp": now,
        }

        # 1. Primary: Webhook
        if self.webhook_url:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            webhook_success = False
            for attempt in range(2):
                try:
                    with urllib.request.urlopen(req, timeout=5.0) as resp:
                        if 200 <= resp.status < 300:
                            webhook_success = True
                            break
                except Exception:
                    if attempt == 0:
                        time.sleep(2.0)

            if webhook_success:
                self._last_alert_ts = now
                return True

        # 2. Fallback: Email SMTP
        if self.email_smtp_host:
            try:
                import smtplib
                from email.mime.text import MIMEText

                msg = MIMEText(f"CRITICAL HEALTH ALERT:\n{json.dumps(payload, indent=2)}")
                msg["Subject"] = f"CRITICAL ALERT - AHFMES-ARE ({health_report.details})"
                msg["From"] = self.email_from or "alerts@ahfmes.local"
                msg["To"] = self.email_to or "admin@ahfmes.local"

                with smtplib.SMTP(self.email_smtp_host, self.email_smtp_port, timeout=5.0) as server:
                    try:
                        server.starttls()
                    except Exception:
                        pass
                    if self.email_user and self.email_password:
                        server.login(self.email_user, self.email_password)
                    server.send_message(msg)

                self._last_alert_ts = now
                return True
            except Exception:
                return False

        return False


class SystemHealthMonitor:
    """
    Local Watchdog monitoring core execution and infrastructure vitals.
    """

    def __init__(self, alert_sender: Optional[CriticalAlertSender] = None):
        self.alert_sender = alert_sender

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
            report = HealthReport(
                status=HealthStatus.CRITICAL,
                memory_mb=round(current_mb, 2),
                heartbeat_ok=heartbeat_ok,
                latency_ok=latency_ok,
                vault_ok=vault_ok,
                details="; ".join(critical_reasons),
            )
            if self.alert_sender is not None:
                self.alert_sender.send_alert(report)
            return report

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

    def get_status(
        self,
        last_tick_ts: Optional[float] = None,
        latencies: Optional[List[float]] = None,
        event_store: Optional[Any] = None,
    ) -> HealthStatus:
        """Convenience method returning current HealthStatus."""
        now = time.time()
        tick_ts = last_tick_ts if last_tick_ts is not None else now
        lats = latencies if latencies is not None else [10.0]
        report = self.evaluate_system_health(
            last_tick_ts=tick_ts,
            latencies=lats,
            event_store=event_store,
            current_time=now,
        )
        return report.status