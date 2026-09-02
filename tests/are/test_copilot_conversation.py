"""
Tests for multi-turn conversation state in the copilot (ConversationSession).

Covers:
- Session creation, history tracking, and cleanup
- Context carryover for follow-up questions
- Backward compatibility (stateless mode unchanged)
- Auto-session creation
- History trimming at max_history
"""

import unittest

from are.copilot import ConversationalCopilot, ConversationSession


class MockServerState:
    def __init__(self):
        self.kill_switch_active = False

    def get_status_payload(self):
        return {
            "champion": {"champion_id": "P001_CHAMPION_V1", "candidate_id": "CAND_ALPHA_001", "status": "ACTIVE"},
            "safety": {"kill_switch_active": self.kill_switch_active, "max_drawdown_pct": 0.15, "volatility_cutoff": 2.5},
            "stream_stats": {"total_ticks": 120, "veto_count": 5, "chain_health": "VERIFIED_OK"},
        }

    def set_kill_switch(self, active: bool):
        self.kill_switch_active = active


class TestConversationSession(unittest.TestCase):
    """Tests for the ConversationSession dataclass."""

    def test_session_creation(self):
        session = ConversationSession(session_id="s1")
        self.assertEqual(session.session_id, "s1")
        self.assertEqual(session.messages, [])
        self.assertEqual(session.max_history, 20)

    def test_add_message(self):
        session = ConversationSession(session_id="s1")
        session.add_message("user", "Halo")
        session.add_message("assistant", "Selamat datang!")
        self.assertEqual(len(session.messages), 2)
        self.assertEqual(session.messages[0], {"role": "user", "content": "Halo"})
        self.assertEqual(session.messages[1], {"role": "assistant", "content": "Selamat datang!"})

    def test_get_history_returns_copy(self):
        session = ConversationSession(session_id="s1")
        session.add_message("user", "test")
        history = session.get_history()
        history.append({"role": "user", "content": "mutated"})
        self.assertEqual(len(session.messages), 1)  # Original unchanged

    def test_max_history_trimming(self):
        session = ConversationSession(session_id="s1", max_history=3)
        for i in range(5):
            session.add_message("user", f"msg-{i}")
        self.assertEqual(len(session.messages), 3)
        self.assertEqual(session.messages[0]["content"], "msg-2")
        self.assertEqual(session.messages[2]["content"], "msg-4")


class TestCopilotConversationState(unittest.TestCase):
    """Tests for multi-turn conversation in ConversationalCopilot."""

    def setUp(self):
        self.state = MockServerState()
        self.copilot = ConversationalCopilot(
            server_state=self.state,
            ollama_url="http://127.0.0.1:19999/api/generate",
            timeout_sec=0.2,
        )

    def test_stateless_mode_unchanged(self):
        """Without session_id, behavior is identical to previous stateless mode."""
        r1 = self.copilot.generate_response("Halo")
        r2 = self.copilot.generate_response("Halo")
        # Both should produce the same deterministic response
        self.assertIn("AI Copilot", r1)
        self.assertIn("AI Copilot", r2)
        # No session should be created
        self.assertEqual(len(self.copilot._sessions), 0)

    def test_session_start_end(self):
        session = self.copilot.start_session("s1")
        self.assertIsInstance(session, ConversationSession)
        self.assertEqual(session.session_id, "s1")
        self.assertIs(self.copilot.get_session("s1"), session)
        self.copilot.end_session("s1")
        self.assertIsNone(self.copilot.get_session("s1"))

    def test_session_records_history(self):
        self.copilot.start_session("s1")
        self.copilot.generate_response("status sistem", session_id="s1")
        session = self.copilot.get_session("s1")
        self.assertEqual(len(session.messages), 2)
        self.assertEqual(session.messages[0]["role"], "user")
        self.assertEqual(session.messages[0]["content"], "status sistem")
        self.assertEqual(session.messages[1]["role"], "assistant")

    def test_auto_session_creation(self):
        """Passing a session_id that doesn't exist auto-creates the session."""
        self.copilot.generate_response("halo", session_id="auto-1")
        session = self.copilot.get_session("auto-1")
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, "auto-1")

    def test_context_carryover_followup(self):
        """Follow-up questions should include context from recent history."""
        self.copilot.start_session("s1")
        # First, establish a topic
        self.copilot.generate_response("status sistem", session_id="s1")
        # Then ask a follow-up that should resolve via context
        session = self.copilot.get_session("s1")
        resolved = session.resolve_followup("apa itu?")
        # The resolved message should contain context reference
        self.assertIn("Konteks percakapan sebelumnya", resolved)
        self.assertIn("Status AHFMES-ARE", resolved)

    def test_kill_switch_works_in_session(self):
        """Kill switch keyword matching should work regardless of session mode."""
        self.copilot.start_session("s1")
        self.copilot.generate_response("kill switch", session_id="s1")
        self.assertTrue(self.state.kill_switch_active)
        self.copilot.generate_response("nyalakan", session_id="s1")
        self.assertFalse(self.state.kill_switch_active)

    def test_multiple_sessions_independent(self):
        """Different sessions should have independent histories."""
        self.copilot.start_session("s1")
        self.copilot.start_session("s2")
        self.copilot.generate_response("status", session_id="s1")
        self.copilot.generate_response("slippage", session_id="s2")
        s1 = self.copilot.get_session("s1")
        s2 = self.copilot.get_session("s2")
        self.assertEqual(len(s1.messages), 2)
        self.assertEqual(len(s2.messages), 2)
        self.assertEqual(s1.messages[0]["content"], "status")
        self.assertEqual(s2.messages[0]["content"], "slippage")


class TestResolveFollowup(unittest.TestCase):
    """Tests for follow-up resolution logic."""

    def test_bare_followup_resolves(self):
        session = ConversationSession(session_id="s1")
        session.add_message("user", "status sistem")
        session.add_message("assistant", "Status AHFMES-ARE: Champion P001, Status AKTIF, Max DD 15%")
        resolved = session.resolve_followup("apa itu?")
        self.assertIn("Konteks percakapan sebelumnya", resolved)
        self.assertIn("Status AHFMES-ARE", resolved)

    def test_normal_message_passes_through(self):
        session = ConversationSession(session_id="s1")
        session.add_message("user", "status")
        session.add_message("assistant", "Status OK")
        resolved = session.resolve_followup("slippage XAUUSD")
        self.assertEqual(resolved, "slippage XAUUSD")

    def test_empty_session_no_resolution(self):
        session = ConversationSession(session_id="s1")
        resolved = session.resolve_followup("apa itu?")
        self.assertEqual(resolved, "apa itu?")


if __name__ == "__main__":
    unittest.main()
