"""
Unit and Integration Tests for AHFMES WEB_UI (ACC-701, ACC-702, ACC-703, ACC-704)
"""

import http.client
import http.server
import json
import os
import tempfile
import threading
import time
import unittest

import are.web_ui as web_ui_module
from are.web_ui import AREAPIHandler, AREServerState


class TestWebUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.tmp_dir.name, "web_test.db")
        cls.state = AREServerState(cls.db_path)
        web_ui_module._GLOBAL_SERVER_STATE = cls.state

        # Start live test server on dynamic ephemeral port
        cls.httpd = http.server.HTTPServer(("127.0.0.1", 0), AREAPIHandler)
        cls.server_port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        if hasattr(cls, 'server_thread') and cls.server_thread.is_alive():
            cls.server_thread.join(timeout=2.0)
        cls.state.close()
        web_ui_module._GLOBAL_SERVER_STATE = None
        import gc
        gc.collect()
        time.sleep(0.1)
        try:
            cls.tmp_dir.cleanup()
        except Exception:
            pass

    def _make_request(self, method: str, path: str, body: dict = None) -> tuple[int, dict | str]:
        conn = http.client.HTTPConnection("127.0.0.1", self.server_port, timeout=10)
        headers = {"Content-Type": "application/json"} if body else {}
        data = json.dumps(body) if body else None
        conn.request(method, path, body=data, headers=headers)
        resp = conn.getresponse()
        resp_data = resp.read().decode("utf-8")
        conn.close()
        try:
            return resp.status, json.loads(resp_data)
        except Exception:
            return resp.status, resp_data

    def test_get_index_html(self):
        status, content = self._make_request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("AHFMES-ARE Control Center", content)

    def test_get_api_status(self):
        status, data = self._make_request("GET", "/api/status")
        self.assertEqual(status, 200)
        self.assertIn("champion", data)
        self.assertIn("safety", data)
        self.assertIn("stream_stats", data)
        self.assertFalse(data["safety"]["kill_switch_active"])

    def test_post_kill_switch_toggle(self):
        # 1. Activate kill switch
        status, data = self._make_request("POST", "/api/kill-switch", {"active": True})
        self.assertEqual(status, 200)
        self.assertTrue(data["kill_switch_active"])
        self.assertTrue(self.state.safety_kernel.limits.kill_switch_active)

        # 2. Deactivate kill switch
        status, data = self._make_request("POST", "/api/kill-switch", {"active": False})
        self.assertEqual(status, 200)
        self.assertFalse(data["kill_switch_active"])
        self.assertFalse(self.state.safety_kernel.limits.kill_switch_active)

    def test_post_step_tick_normal_and_shock(self):
        # Step normal tick
        status, data = self._make_request("POST", "/api/step-tick", {
            "symbol": "BTCUSD",
            "price": 65100.0,
            "volatility": 1.0,
            "is_shock": False,
        })
        self.assertEqual(status, 200)
        self.assertIn("signal", data)
        self.assertIn("allowed", data)

        # Step shock tick
        status_shock, data_shock = self._make_request("POST", "/api/step-tick", {
            "symbol": "BTCUSD",
            "price": 64000.0,
            "volatility": 3.5,
            "is_shock": True,
        })
        self.assertEqual(status_shock, 200)
        self.assertTrue(data_shock["is_shock"])

    def test_post_chat_copilot(self):
        # Test status inquiry
        status, data = self._make_request("POST", "/api/chat", {"message": "Status sistem saat ini?"})
        self.assertEqual(status, 200)
        self.assertIn("Active Champion", data["reply"])

        # Test kill switch trigger via chat
        status, data_kill = self._make_request("POST", "/api/chat", {"message": "Aktifkan kill switch darurat"})
        self.assertEqual(status, 200)
        self.assertIn("EMERGENCY KILL SWITCH", data_kill["reply"])
        self.assertTrue(self.state.safety_kernel.limits.kill_switch_active)

    def test_post_run_research_cycle(self):
        status, data = self._make_request("POST", "/api/run-cycle", {"symbol": "BTCUSD"})
        self.assertEqual(status, 200)
        self.assertEqual(data["symbol"], "BTCUSD")
        self.assertEqual(data["program_status"], "SUCCESS")
        self.assertIsNotNone(data["promoted_champion"])


if __name__ == "__main__":
    unittest.main()
