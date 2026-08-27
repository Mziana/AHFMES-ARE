"""
AHFMES ARE-3 — Isolated Capability Sandbox (Slice-2 Part B)

Implements:
- SandboxSecurityViolation & SandboxTimeoutError (fail-closed exceptions).
- SandboxExecutionResult: immutable execution telemetry container.
- CapabilitySandbox: isolated runtime environment blocking network/socket I/O (ACC-311)
  and bounding execution duration with fail-closed timeout (ACC-312).

Zero external dependencies (stdlib only).
"""

from __future__ import annotations

import socket
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple


class SandboxSecurityViolation(Exception):
    """Raised when sandbox detects unauthorized access (e.g., network / socket I/O)."""
    pass


class SandboxTimeoutError(Exception):
    """Raised when execution duration exceeds permitted timeout threshold (fail-closed)."""
    pass


@dataclass(frozen=True)
class SandboxExecutionResult:
    success: bool
    output: Any
    error: Optional[str]
    execution_time_ms: float
    memory_bytes: int
    violation_detected: bool


def _blocked_socket(*args, **kwargs):
    raise SandboxSecurityViolation("Network / Socket access is strictly forbidden in CapabilitySandbox (ACC-311)")


class CapabilitySandbox:
    """
    Isolated execution container for capability evaluation.
    Enforces zero network access and strict execution timeouts.
    """

    def __init__(self, default_timeout_sec: float = 2.0):
        self.default_timeout_sec = default_timeout_sec

    def execute(
        self,
        func: Callable,
        args: Tuple[Any, ...] = (),
        kwargs: Optional[Dict[str, Any]] = None,
        timeout_sec: Optional[float] = None,
    ) -> SandboxExecutionResult:
        """
        Executes func(*args, **kwargs) inside security sandbox.
        Fails-closed on security violation or timeout.
        """
        if kwargs is None:
            kwargs = {}
        timeout = timeout_sec if timeout_sec is not None else self.default_timeout_sec

        result_container: Dict[str, Any] = {
            "output": None,
            "error": None,
            "exception": None,
            "success": False,
            "violation": False,
        }

        # Backup sensitive stdlib symbols
        orig_socket = socket.socket
        orig_urlopen = getattr(urllib.request, "urlopen", None)

        def runner():
            try:
                # Mock socket creation to raise SandboxSecurityViolation
                socket.socket = _blocked_socket
                if orig_urlopen is not None:
                    urllib.request.urlopen = _blocked_socket

                res = func(*args, **kwargs)
                result_container["output"] = res
                result_container["success"] = True
            except SandboxSecurityViolation as ssv:
                result_container["violation"] = True
                result_container["exception"] = ssv
                result_container["error"] = str(ssv)
            except Exception as e:
                result_container["exception"] = e
                result_container["error"] = str(e)
            finally:
                # Restore original symbols
                socket.socket = orig_socket
                if orig_urlopen is not None:
                    urllib.request.urlopen = orig_urlopen

        start_time = time.perf_counter()
        thread = threading.Thread(target=runner)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Always ensure symbols are restored even if thread is stuck
        socket.socket = orig_socket
        if orig_urlopen is not None:
            urllib.request.urlopen = orig_urlopen

        if thread.is_alive():
            raise SandboxTimeoutError(
                f"Capability execution timed out after {timeout:.2f}s (ACC-312)"
            )

        if result_container["violation"]:
            raise result_container["exception"]

        output = result_container["output"]
        mem_bytes = sys.getsizeof(output) if output is not None else 0

        return SandboxExecutionResult(
            success=result_container["success"],
            output=output,
            error=result_container["error"],
            execution_time_ms=duration_ms,
            memory_bytes=mem_bytes,
            violation_detected=result_container["violation"],
        )
