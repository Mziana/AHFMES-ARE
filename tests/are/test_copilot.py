"""
Unit and Integration Tests for ARE AI Copilot & Ollama Integration (ACC-716)
"""

import http.server
import json
import os
import threading
import time
import unittest
from are.copilot import ConversationalCopilot


class MockServerState:
    """Mock AREServerState container for Copilot testing."""

    def __init__(self):
        self.kill_switch_active = False

    def get_status_payload(self):
        return {
            "champion": {
                "champion_id": "P001_CHAMPION_V1",
                "candidate_id": "CAND_ALPHA_001",
                "status": "ACTIVE",
            },
            "safety": {
                "kill_switch_active": self.kill_switch_active,
                "max_drawdown_pct": 0.15,
                "volatility_cutoff": 2.5,
            },
            "stream_stats": {
                "total_ticks": 120,
                "veto_count": 5,
                "chain_health": "VERIFIED_OK",
            },
        }

    def set_kill_switch(self, active: bool):
        self.kill_switch_active = active
        return self.kill_switch_active


class MockOllamaHandler(http.server.BaseHTTPRequestHandler):
    """Mock handler simulating local Ollama API with generate & tags support."""

    def do_GET(self):
        if self.path in ("/api/tags", "/api/tags/"):
            resp_payload = {
                "models": [
                    {"name": "deepseek-coder:6.7b"},
                    {"name": "qwen2.5-coder:latest"},
                ]
            }
            body = json.dumps(resp_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8")
        try:
            req_json = json.loads(post_data)
            prompt = req_json.get("prompt", "")
            resp_payload = {
                "model": req_json.get("model", "qwen2.5-coder"),
                "response": f"[QWEN_GENERATED] Respon tergenerasi dari model untuk: {prompt[-30:]}",
                "done": True,
            }
            body = json.dumps(resp_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True
        except Exception:
            self.send_response(500)
            self.end_headers()


class TestCopilot(unittest.TestCase):
    def setUp(self):
        self.state = MockServerState()
        # Default with non-existent port to test offline fallback
        self.copilot = ConversationalCopilot(
            server_state=self.state,
            ollama_url="http://127.0.0.1:19999/api/generate",
            timeout_sec=0.2,
        )

    def test_copilot_empty_message(self):
        reply = self.copilot.generate_response("")
        self.assertIn("Silakan ajukan pertanyaan", reply)

    def test_copilot_greeting_and_identity(self):
        reply = self.copilot.generate_response("Halo, siapa kamu?")
        self.assertIn("AI Copilot", reply)

    def test_copilot_expanded_identity(self):
        reply = self.copilot.generate_response("ceritakan tentang dirimu")
        self.assertIn("AI Copilot AHFMES-ARE Control Center", reply)
        self.assertIn("Autonomous Research Engine", reply)
        self.assertIn("Capital Safety Kernel", reply)
        self.assertIn("MetaTrader 5", reply)

    def test_copilot_mt5_and_xauusd_inquiry(self):
        # Spaced MT 5 and XAU USD query
        reply = self.copilot.generate_response("apa kamu bisa mengakses dan membuka MT 5 untuk pair XAU USD?")
        self.assertIn("Integrasi MetaTrader 5 (MT5)", reply)
        self.assertIn("are/mt5_feed.py", reply)
        self.assertIn("are/mt5_gateway.py", reply)
        self.assertIn("XAUUSD", reply)

    def test_copilot_buka_pasar_xauusd(self):
        reply = self.copilot.generate_response("buka pasar xauusd")
        self.assertIn("Integrasi MetaTrader 5 (MT5)", reply)
        self.assertIn("XAUUSD", reply)

    def test_copilot_status_inquiry(self):
        reply = self.copilot.generate_response("Bagaimana status sistem saat ini?")
        self.assertIn("Active Champion", reply)
        self.assertIn("P001_CHAMPION_V1", reply)
        self.assertIn("Max Drawdown Limit", reply)

    def test_copilot_quant_strategies_inquiry(self):
        reply = self.copilot.generate_response("Jelaskan strategi RSI scalping dan orderbook imbalance")
        self.assertIn("RSI / Momentum", reply)
        self.assertIn("Orderbook Imbalance", reply)
        self.assertIn("Mean Reversion", reply)

    def test_copilot_kill_switch_trigger_activate_and_deactivate(self):
        # 1. Activate kill switch via chat
        reply = self.copilot.generate_response("Aktifkan emergency kill switch sekarang!")
        self.assertIn("EMERGENCY KILL SWITCH TELAH DIAKTIFKAN", reply)
        self.assertTrue(self.state.kill_switch_active)

        # 2. Deactivate kill switch via chat
        reply_deact = self.copilot.generate_response("Hidupkan kembali sistem normal")
        self.assertIn("Kill Switch dinonaktifkan", reply_deact)
        self.assertFalse(self.state.kill_switch_active)

    def test_copilot_generic_question_non_robotic_fallback(self):
        reply = self.copilot.generate_response("Berapa temperatur di Tokyo saat ini?")
        self.assertIn("Analisis Kontekstual AHFMES-ARE", reply)
        self.assertNotIn("Saya memahami pertanyaan Anda", reply)
        self.assertIn("P001_CHAMPION_V1", reply)

    def test_copilot_ollama_online_mock_integration_and_model_discovery(self):
        # Start ephemeral mock Ollama HTTP server
        mock_server = http.server.HTTPServer(("127.0.0.1", 0), MockOllamaHandler)
        mock_port = mock_server.server_address[1]
        server_thread = threading.Thread(target=mock_server.serve_forever, daemon=True)
        server_thread.start()
        time.sleep(0.05)

        try:
            online_copilot = ConversationalCopilot(
                server_state=self.state,
                ollama_url=f"http://127.0.0.1:{mock_port}/api/generate",
                timeout_sec=2.0,
            )
            # 1. Test model auto discovery
            discovered = online_copilot._discover_ollama_model()
            self.assertEqual(discovered, "qwen2.5-coder:latest")

            # 2. Test response generation
            reply = online_copilot.generate_response("Analisis likuiditas pasar terkini")
            self.assertIn("[QWEN_GENERATED]", reply)
        finally:
            mock_server.shutdown()
            mock_server.server_close()


if __name__ == "__main__":
    unittest.main()
