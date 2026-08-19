"""
Application state model for CodeTyper.
Provides an explicit state machine for coordinating UI sensitivity and actions.
"""

from enum import Enum, auto


class AppState(Enum):
    """Lifecycle states of the CodeTyper application."""

    IDLE = auto()
    COUNTDOWN = auto()
    TYPING = auto()
