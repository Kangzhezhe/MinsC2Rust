"""Background thread that listens for the Escape key in raw terminal mode.

Matches claude-code-main's AbortController pattern: when ESC is detected,
the listener calls an on_cancel callback that can abort the active HTTP
stream immediately, rather than waiting for the next yield point.

Uses os.read() (unbuffered) instead of sys.stdin.read() to avoid
mismatches between Python's I/O buffer and select(), which operates
on the raw file descriptor.
"""
from __future__ import annotations

import os
import sys
import select
import threading
from typing import Callable

try:
    import termios
    import tty
    _HAS_TERMIOS = True
except ImportError:
    _HAS_TERMIOS = False


class EscListener:
    """Context manager that listens for ESC in a daemon thread.

    Usage:
        def cancel():
            engine.cancel_turn()

        listener = EscListener(on_cancel=cancel)
        with listener:
            for event in engine.submit(user_input):
                if listener.pressed:
                    break
                ...

    While active, the terminal is in cbreak mode. Call ``pause()`` before
    reading interactive input (e.g. permission prompts), and ``resume()``
    after, so the listener thread doesn't steal keystrokes.
    """

    def __init__(self, on_cancel: Callable[[], None] | None = None):
        self.pressed = False
        self._on_cancel = on_cancel
        self._stop = threading.Event()
        self._paused = threading.Event()   # set = paused, clear = running
        self._thread: threading.Thread | None = None
        self._old_settings = None
        self._fd = sys.stdin.fileno()

    # -- context manager --------------------------------------------------

    def __enter__(self):
        self.pressed = False
        self._stop.clear()
        self._paused.clear()
        # Save terminal settings and switch to cbreak mode
        # (chars available immediately, Ctrl+C still raises KeyboardInterrupt)
        self._old_settings = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        # Restore terminal
        if self._old_settings is not None:
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._old_settings)
            self._old_settings = None

    # -- pause/resume for interactive input --------------------------------

    def pause(self):
        """Pause the listener so stdin can be read by permission prompts."""
        self._paused.set()

    def resume(self):
        """Resume listening after interactive input is done."""
        self._paused.clear()

    # -- non-blocking ESC check for main thread ----------------------------

    def check_esc_nonblocking(self) -> bool:
        """Check for ESC from the main thread without blocking.

        Call this between event yields when the main thread is NOT blocked
        (e.g. during streaming). The background thread should be paused
        during this time to avoid both threads reading stdin.

        Returns True if ESC was detected.
        """
        if self.pressed:
            return True
        while self._has_data(0):
            b = os.read(self._fd, 1)
            if b == b'\x1b':
                if self._has_data(0.05):
                    self._drain()
                    continue
                self.pressed = True
                if self._on_cancel:
                    self._on_cancel()
                return True
            # Non-ESC: discard
        return False

    # -- internal ---------------------------------------------------------

    def _read_byte(self) -> bytes:
        """Read a single byte directly from the fd (unbuffered)."""
        return os.read(self._fd, 1)

    def _has_data(self, timeout: float) -> bool:
        """Check if the fd has data available within timeout seconds."""
        return bool(select.select([self._fd], [], [], timeout)[0])

    def _drain(self):
        """Drain all immediately available bytes from the fd."""
        while self._has_data(0.01):
            os.read(self._fd, 64)

    def _listen(self):
        while not self._stop.is_set():
            # If paused, just sleep and check again
            if self._paused.is_set():
                self._stop.wait(0.05)
                continue

            if not self._has_data(0.05):
                continue
            if self._paused.is_set():
                continue

            b = self._read_byte()
            if b == b'\x1b':
                # Distinguish bare ESC from escape sequences (arrow
                # keys, F-keys, Alt+X, etc.) which all start with
                # \x1b but are followed by more bytes immediately.
                if self._has_data(0.05):
                    # Escape sequence — drain remaining bytes and ignore
                    self._drain()
                    continue
                # No follow-up bytes → genuine ESC press
                self.pressed = True
                if self._on_cancel:
                    self._on_cancel()
                return
            # Non-ESC byte: ignore (already consumed).
            # This is fine because the listener is only active when
            # no interactive input is expected.


# ---------------------------------------------------------------------------
# Windows fallback: termios/tty are Unix-only; use msvcrt instead.
# ---------------------------------------------------------------------------
if not _HAS_TERMIOS:
    import msvcrt

    class EscListener:  # type: ignore[no-redef]
        """Windows version of EscListener using msvcrt (no terminal raw mode needed)."""

        def __init__(self, on_cancel: Callable[[], None] | None = None):
            self.pressed = False
            self._on_cancel = on_cancel
            self._stop = threading.Event()
            self._paused = threading.Event()   # set = paused, clear = running
            self._thread: threading.Thread | None = None

        # -- context manager --------------------------------------------------

        def __enter__(self):
            self.pressed = False
            self._stop.clear()
            self._paused.clear()
            self._thread = threading.Thread(target=self._listen, daemon=True)
            self._thread.start()
            return self

        def __exit__(self, *_exc):
            self._stop.set()
            if self._thread is not None:
                self._thread.join(timeout=0.5)

        # -- pause/resume for interactive input --------------------------------

        def pause(self):
            """Pause the listener so stdin can be read by permission prompts."""
            self._paused.set()

        def resume(self):
            """Resume listening after interactive input is done."""
            self._paused.clear()

        # -- non-blocking ESC check for main thread ----------------------------

        def check_esc_nonblocking(self) -> bool:
            if self.pressed:
                return True
            while msvcrt.kbhit():
                if msvcrt.getch() == b'\x1b':
                    self.pressed = True
                    if self._on_cancel:
                        self._on_cancel()
                    return True
            return False

        # -- internal ---------------------------------------------------------

        def _listen(self):
            while not self._stop.is_set():
                # If paused, just sleep and check again
                if self._paused.is_set():
                    self._stop.wait(0.05)
                    continue
                if not msvcrt.kbhit():
                    self._stop.wait(0.05)
                    continue
                if self._paused.is_set():
                    continue
                if msvcrt.getch() == b'\x1b':
                    self.pressed = True
                    if self._on_cancel:
                        self._on_cancel()
                    return
