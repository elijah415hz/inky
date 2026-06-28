"""Drives which page is shown on the Inky display and switches between pages.

This module is deliberately free of any GPIO / hardware imports so it can be
unit-tested off-device. The on-device entrypoint (``main.py``) owns the button
wiring and simply calls :meth:`PageController.request` from a button handler.
"""
import threading
from typing import Dict, Optional

from pages.basePage import BasePage


class PageController:
    """Holds the page registry and renders the active page in a loop.

    Pages are keyed by button label ("A".."D"). A button press calls
    :meth:`request`, which wakes the render loop so the switch (or a forced
    refresh of the current page) happens immediately rather than after the
    page's ``refresh_rate``.
    """

    def __init__(self, pages: Dict[str, BasePage], start_key: str):
        if start_key not in pages:
            raise ValueError(f"start_key {start_key!r} is not a registered page")
        self.pages = pages
        self.current_key = start_key
        self.current_page = pages[start_key]
        self._wake = threading.Event()
        self._requested_key: Optional[str] = None
        self._lock = threading.Lock()

    def request(self, label: str) -> None:
        """Ask the loop to show the page bound to ``label``.

        Unknown labels (buttons with no assigned page) are ignored. Requesting
        the page that is already showing forces an immediate re-render.
        """
        if label not in self.pages:
            return
        with self._lock:
            self._requested_key = label
        self._wake.set()

    def cycle(self) -> None:
        """Advance to the next registered page in order, wrapping around.

        For a button that isn't bound to a specific page: lets one button step
        through every page. Steps from a pending request if one is queued, so
        rapid presses advance through pages instead of toggling in place.
        """
        keys = list(self.pages)
        with self._lock:
            base = self._requested_key or self.current_key
        nxt = keys[(keys.index(base) + 1) % len(keys)]
        self.request(nxt)

    def _apply_request(self) -> None:
        with self._lock:
            requested = self._requested_key
            self._requested_key = None
        if requested is None:
            return
        if requested != self.current_key:
            self.current_page.unload_page()
            self.current_key = requested
            self.current_page = self.pages[requested]
            self.current_page.load_page()
        # Same key -> fall through; the loop re-renders the current page.

    def render_once(self, display) -> None:
        """Render the active page to the display a single time."""
        display.set_image(self.current_page.make_image())
        display.show()

    def run(self, display) -> None:
        """Render forever, waking early when a button is pressed."""
        self.current_page.load_page()
        while True:
            self.render_once(display)
            self._wake.wait(timeout=self.current_page.refresh_rate)
            self._wake.clear()
            self._apply_request()
