"""Callback registration stubs."""

# Callback functions would normally register with the Dash ``app`` instance.
# The real callback implementations have not been ported yet, so this module
# simply exposes the application object for compatibility.
from .app import app  # noqa: F401

__all__ = []
