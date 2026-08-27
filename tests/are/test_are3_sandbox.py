"""
Unit Tests for AHFMES ARE-3 Capability Sandbox (ACC-311, ACC-312)
"""

import socket
import time
import unittest
import urllib.request

from are.sandbox import CapabilitySandbox, SandboxExecutionResult, SandboxSecurityViolation, SandboxTimeoutError


class TestCapabilitySandbox(unittest.TestCase):
    def setUp(self):
        self.sandbox = CapabilitySandbox(default_timeout_sec=1.0)

    def test_pure_function_execution_success(self):
        def add(a, b):
            return a + b

        res = self.sandbox.execute(add, args=(10, 25))
        self.assertIsInstance(res, SandboxExecutionResult)
        self.assertTrue(res.success)
        self.assertEqual(res.output, 35)
        self.assertIsNone(res.error)
        self.assertFalse(res.violation_detected)

    def test_socket_creation_blocked(self):
        def attempt_network():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            return s

        with self.assertRaises(SandboxSecurityViolation):
            self.sandbox.execute(attempt_network)

    def test_urlopen_blocked(self):
        def attempt_http():
            return urllib.request.urlopen("http://127.0.0.1:8080")

        with self.assertRaises(SandboxSecurityViolation):
            self.sandbox.execute(attempt_http)

    def test_timeout_fail_closed(self):
        def infinite_loop():
            time.sleep(2.0)
            return "done"

        with self.assertRaises(SandboxTimeoutError):
            self.sandbox.execute(infinite_loop, timeout_sec=0.2)


if __name__ == "__main__":
    unittest.main()
