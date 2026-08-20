"""
Audio and acoustic feedback utilities for CodeWriter.
Provides non-blocking chime and countdown tick cues via GDK / system display bell.
"""

import logging
from typing import Optional

import gi

gi.require_version("Gdk", "4.0")
from gi.repository import Gdk

logger = logging.getLogger("CodeWriter.Sound")


def play_chime() -> None:
    """Trigger an audio bell chime on typing completion."""
    try:
        display = Gdk.Display.get_default()
        if display:
            display.beep()
    except Exception as e:
        logger.debug(f"Could not play audio chime: {e}")


def play_tick() -> None:
    """Trigger a subtle acoustic cue on countdown tick."""
    try:
        display = Gdk.Display.get_default()
        if display:
            display.beep()
    except Exception as e:
        logger.debug(f"Could not play audio tick: {e}")
