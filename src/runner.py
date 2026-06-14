"""Execute a curl command string and capture its output."""

from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 120  # seconds; use curl's --max-time for finer control


@dataclass
class CurlResult:
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    def as_text(self) -> str:
        """Human-readable result for a Telegram message."""
        if self.ok:
            return self.stdout.strip() or "(empty response)"
        body = self.stderr.strip() or self.stdout.strip() or "(no output)"
        return f"[curl exited {self.returncode}]\n{body}"


def _run_argv(argv: list[str], timeout: int = DEFAULT_TIMEOUT) -> CurlResult:
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CurlResult(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except subprocess.TimeoutExpired:
        return CurlResult(returncode=-1, stdout="", stderr=f"curl timed out after {timeout}s")
    except FileNotFoundError:
        return CurlResult(returncode=-1, stdout="", stderr="curl binary not found")
    except OSError as exc:
        return CurlResult(returncode=-1, stdout="", stderr=f"failed to run curl: {exc}")


def run_curl(curl_str: str, timeout: int = DEFAULT_TIMEOUT, proxy: str | None = None) -> CurlResult:
    """Run ``curl_str`` and optionally force a proxy with ``--proxy``.

    If the command already includes ``-x`` or ``--proxy``, it is left unchanged.
    """
    try:
        argv = shlex.split(curl_str)
    except ValueError as exc:
        return CurlResult(returncode=-1, stdout="", stderr=f"Invalid curl command: {exc}")

    if not argv or argv[0] != "curl":
        return CurlResult(returncode=-1, stdout="", stderr="Command must start with 'curl'")

    if proxy and "-x" not in argv and "--proxy" not in argv:
        argv = [argv[0], "--proxy", proxy, *argv[1:]]

    return _run_argv(argv, timeout=timeout)
