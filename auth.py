"""Authenticated browser lifecycle helpers for Kalvium automation."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    sync_playwright,
)

PROFILE_DIRECTORY = Path(__file__).parent / "playwright-profile"


@contextmanager
def open_browser() -> Iterator[tuple[BrowserContext, Page]]:
    """Open the existing authenticated Chrome profile and yield its context and page.

    The function never performs login or modifies authentication state.  Closing the
    context and Playwright instance on exit releases the profile lock cleanly.
    """
    if not PROFILE_DIRECTORY.is_dir():
        raise FileNotFoundError(
            f"Playwright profile directory does not exist: {PROFILE_DIRECTORY}"
        )

    playwright: Playwright = sync_playwright().start()
    context: BrowserContext | None = None
    try:
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(PROFILE_DIRECTORY),
                channel="chrome",
                headless=False,
            )
        except PlaywrightError as exc:
            if "existing browser session" in str(exc):
                raise RuntimeError(
                    "The Playwright profile is already open. Close every Chrome "
                    "window using playwright-profile before starting the MCP server."
                ) from exc
            raise RuntimeError("Chrome could not be launched with the Playwright profile.") from exc
        page = context.pages[0] if context.pages else context.new_page()
        yield context, page
    finally:
        if context is not None:
            context.close()
        playwright.stop()
