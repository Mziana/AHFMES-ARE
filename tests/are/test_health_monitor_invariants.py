"""
Local System Health Monitor & Circuit Breaker Invariant Tests (DELEGASI_033, ACC-406)
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest

from are.health_monitor import HealthReport, HealthStatus, SystemHealthMonitor
from are.safety import CapitalSafetyKernel
from are.storage import EventStore


class TestHealthMonitorInvariants(unittest.TestCase):
    def setUp(self):
        self.monitor = SystemHealthMonitor()
        self.csk = CapitalSafetyKernel()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "health_test.db")

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_mt5_hang_triggers_critical_veto(self):
        """
        Invariant 1: MT5 silence > 10s MUST flag CRITICAL and trigger EMERGENCY_FLAT in CSK.
        """
        now = time.time()
        last_tick = now - 20.0  # 20 seconds silence (hang)

        # 1. Direct heartbeat check
        hb_ok = self.monitor.check_mt5_heartbeat(
            last_tick_timestamp=last_tick,
            max_silence_seconds=10.0,
            current_time=now,
        )
        self.assertFalse(hb_ok, "MT5 heartbeat should report False on 20s silence")

        # 2. Overall health evaluation
        report = self.monitor.evaluate_system_health(
            last_tick_ts=last_tick,
            latencies=[20.0, 35.0],
            current_time=now,
        )
        self.assertEqual(report.status, HealthStatus.CRITICAL)
        self.assertIn("MT5 Heartbeat", report.details)

        # 3. CSK Circuit Breaker Veto
        action = {"action": "BUY", "size": 1.0, "price": 100.0}
        decision = self.csk.evaluate_action(
            intended_action=action,
            current_drawdown=0.01,
            current_volatility=0.01,
            recent_order_count=1,
            health_status=report.status,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "EMERGENCY_FLAT")
        self.assertEqual(decision.clamped_size, 0.0)
        self.assertIn("SYSTEM_HEALTH_CRITICAL", decision.reason)

    def test_memory_usage_check_and_threshold(self):
        """
        Invariant 2: Memory exceeding threshold triggers unhealthy flag.
        """
        # Unreasonably tiny threshold (0.001 MB = 1 KB)
        is_healthy_tiny, mem_mb = self.monitor.check_memory_usage(threshold_mb=0.001)
        self.assertFalse(is_healthy_tiny)
        self.assertGreater(mem_mb, 0.0)

        # Generous threshold (16384 MB = 16 GB)
        is_healthy_large, _ = self.monitor.check_memory_usage(threshold_mb=16384.0)
        self.assertTrue(is_healthy_large)

    def test_latency_spike_veto(self):
        """
        Invariant 3: Latencies > 5000ms or average > 2000ms trigger CRITICAL health state.
        """
        # Single spike > 5000ms
        lat_spike = [100.0, 5500.0, 150.0]
        self.assertFalse(self.monitor.check_latency_spike(lat_spike, max_avg_latency_ms=2000.0))

        report_spike = self.monitor.evaluate_system_health(
            last_tick_ts=time.time(),
            latencies=lat_spike,
        )
        self.assertEqual(report_spike.status, HealthStatus.CRITICAL)

        # High average latency > 2000ms
        lat_high_avg = [2500.0, 2200.0, 2300.0]
        self.assertFalse(self.monitor.check_latency_spike(lat_high_avg, max_avg_latency_ms=2000.0))

        report_avg = self.monitor.evaluate_system_health(
            last_tick_ts=time.time(),
            latencies=lat_high_avg,
        )
        self.assertEqual(report_avg.status, HealthStatus.CRITICAL)

    def test_vault_integrity_integration(self):
        """
        Invariant 4: Vault integrity status seamlessly communicates with SystemHealthMonitor.
        """
        store = EventStore(self.db_path)
        # Commit 2 events
        for i in range(1, 3):
            store.append_event(
                stream_id="health_stream",
                event_data=f"event_{i}".encode("utf-8"),
                expected_revision=i - 1,
                prev_event_hash="0" * 64 if i == 1 else store.get_head("health_stream")[1],
            )

        # Healthy vault
        self.assertTrue(self.monitor.check_vault_integrity(store))

        # Tamper sqlite cache directly behind EventStore's back
        raw_conn = sqlite3.connect(self.db_path)
        with raw_conn:
            raw_conn.execute("DROP TRIGGER IF EXISTS events_no_update;")
            raw_conn.execute("UPDATE events SET event_data = X'deadbeef' WHERE revision = 1;")
        raw_conn.close()

        # Vault integrity check must detect mismatch
        self.assertFalse(self.monitor.check_vault_integrity(store))

        # Overall health should report CRITICAL
        report = self.monitor.evaluate_system_health(
            last_tick_ts=time.time(),
            latencies=[10.0, 15.0],
            event_store=store,
        )
        self.assertEqual(report.status, HealthStatus.CRITICAL)
        self.assertIn("Vault Integrity", report.details)
        store.close()


if __name__ == "__main__":
    unittest.main()