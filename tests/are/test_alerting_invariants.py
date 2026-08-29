"""
Critical External Alerting Invariant Tests (DELEGASI_035B)
100% Mocked Network Isolation (urllib.request.urlopen and smtplib.SMTP). Zero Outbound Calls.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from are.health_monitor import CriticalAlertSender, HealthReport, HealthStatus, SystemHealthMonitor


class TestAlertingInvariants(unittest.TestCase):
    def setUp(self):
        self.critical_report = HealthReport(
            status=HealthStatus.CRITICAL,
            memory_mb=120.0,
            heartbeat_ok=False,
            latency_ok=False,
            vault_ok=True,
            details="MT5 Heartbeat Silence (>10s); Extreme Latency Spike",
        )
        self.healthy_report = HealthReport(
            status=HealthStatus.HEALTHY,
            memory_mb=65.0,
            heartbeat_ok=True,
            latency_ok=True,
            vault_ok=True,
            details="System nominal",
        )

    @patch("urllib.request.urlopen")
    def test_send_critical_alert_returns_true_for_successful_webhook(self, mock_urlopen):
        """
        Invariant 1: Webhook dispatch succeeds and returns True on 200 OK.
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        sender = CriticalAlertSender(webhook_url="https://api.telegram.org/bot123/sendMessage")
        success = sender.send_alert(self.critical_report, champion_id="CHAMP_01", evidence_hash="a" * 64)

        self.assertTrue(success)
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("smtplib.SMTP")
    @patch("urllib.request.urlopen")
    def test_send_critical_alert_returns_false_for_failed_webhook_and_tries_email(
        self, mock_urlopen, mock_smtp
    ):
        """
        Invariant 2: When webhook fails, falls back to SMTP email.
        """
        mock_urlopen.side_effect = Exception("Network Connection Refused")
        mock_smtp_instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_smtp_instance

        sender = CriticalAlertSender(
            webhook_url="https://api.telegram.org/bot123/sendMessage",
            email_smtp_host="smtp.gmail.com",
            email_to="risk_officer@fund.com",
        )

        with patch("time.sleep", return_value=None):
            success = sender.send_alert(self.critical_report, champion_id="CHAMP_01")

        self.assertTrue(success)
        mock_smtp.assert_called_once()
        mock_smtp_instance.send_message.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_rate_limiting_prevents_spam(self, mock_urlopen):
        """
        Invariant 3: Rate limiting prevents spamming (10 calls in 1 minute only sends 1).
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        sender = CriticalAlertSender(
            webhook_url="https://hooks.slack.com/services/T00/B00/X00",
            rate_limit_seconds=300.0,
        )

        sent_count = 0
        base_time = 1700000000.0
        for i in range(10):
            # 10 calls spaced 5 seconds apart (50s total < 300s window)
            current_t = base_time + (i * 5.0)
            if sender.send_alert(self.critical_report, current_time=current_t):
                sent_count += 1

        self.assertEqual(sent_count, 1, "Rate limiting must only allow 1 alert within 300s window")
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("urllib.request.urlopen")
    def test_alert_only_for_critical(self, mock_urlopen):
        """
        Invariant 4: Alerts are only dispatched for CRITICAL status (HEALTHY returns False).
        """
        sender = CriticalAlertSender(webhook_url="https://webhook.site/test")
        res = sender.send_alert(self.healthy_report)

        self.assertFalse(res)
        mock_urlopen.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_alert_includes_evidence_hash(self, mock_urlopen):
        """
        Invariant 5: Alert payload includes cryptographic evidence_hash.
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        sender = CriticalAlertSender(webhook_url="https://webhook.site/test")
        ev_hash = "beef" * 16
        sender.send_alert(self.critical_report, evidence_hash=ev_hash)

        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode("utf-8"))

        self.assertEqual(payload["evidence_hash"], ev_hash)
        self.assertEqual(payload["status"], "CRITICAL")
        self.assertIn("MT5 Heartbeat", payload["details"])

    @patch("urllib.request.urlopen")
    def test_health_monitor_triggers_alert_sender_on_critical(self, mock_urlopen):
        """
        Invariant 6: SystemHealthMonitor automatically invokes CriticalAlertSender on CRITICAL status.
        """
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        sender = CriticalAlertSender(webhook_url="https://webhook.site/test")
        monitor = SystemHealthMonitor(alert_sender=sender)

        # Trigger critical latency (>5000ms)
        report = monitor.evaluate_system_health(
            last_tick_ts=1700000000.0,
            latencies=[6000.0],
            current_time=1700000005.0,
        )

        self.assertEqual(report.status, HealthStatus.CRITICAL)
        mock_urlopen.assert_called_once()


if __name__ == "__main__":
    unittest.main()