"""Authenticated browser lifecycle helpers for Kalvium automation."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import (
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    sync_playwright,
)


PROJECT_DIRECTORY = Path(__file__).resolve().parent
PROFILE_DIRECTORY = PROJECT_DIRECTORY / "profiles" / "default"
LEGACY_PROFILE_DIRECTORY = PROJECT_DIRECTORY / "playwright-profile"


def ensure_profile_directory() -> Path:
    """Return the default profile directory, migrating the legacy one if needed."""
    PROFILE_DIRECTORY.parent.mkdir(parents=True, exist_ok=True)

    if PROFILE_DIRECTORY.exists():
        if not PROFILE_DIRECTORY.is_dir():
            raise NotADirectoryError(
                f"Default Playwright profile path is not a directory: "
                f"{PROFILE_DIRECTORY}"
            )
        return PROFILE_DIRECTORY

    if LEGACY_PROFILE_DIRECTORY.exists():
        if not LEGACY_PROFILE_DIRECTORY.is_dir():
            raise NotADirectoryError(
                "Legacy Playwright profile path is not a directory: "
                f"{LEGACY_PROFILE_DIRECTORY}"
            )

        LEGACY_PROFILE_DIRECTORY.rename(PROFILE_DIRECTORY)

    else:
        PROFILE_DIRECTORY.mkdir()

    return PROFILE_DIRECTORY


def first_time_login() -> None:
    """Open Kalvium in the persistent profile and wait for an interactive login."""
    profile_directory = ensure_profile_directory()

    playwright: Playwright = sync_playwright().start()
    context: BrowserContext | None = None

    try:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_directory),
            channel="chrome",
            headless=False,
        )

        page = context.pages[0] if context.pages else context.new_page()

        page.goto(
            "https://app.kalvium.community",
            wait_until="domcontentloaded",
        )

        print("----------------------------------")
        print("Kalvium Login Required")
        print("----------------------------------")
        print()
        print("Please log into your Kalvium account.")
        print()
        print("When you can see your dashboard,")
        print("return to this terminal and press ENTER.")
        input()

        if "login" in urlparse(page.url).path.lower():
            raise RuntimeError("Login was not completed.")

        print("\u2713 Login successful")

    finally:
        if context is not None:
            try:
                context.close()
            except PlaywrightError:
                pass

        try:
            playwright.stop()
        except PlaywrightError:
            pass


@contextmanager
def open_browser() -> Iterator[tuple[BrowserContext, Page]]:
    """Open the existing authenticated Chrome profile.

    This function never performs login or modifies authentication state.
    """

    profile_directory = ensure_profile_directory()

    playwright: Playwright = sync_playwright().start()
    context: BrowserContext | None = None

    try:
        try:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_directory),
                channel="chrome",
                headless=False,
            )

        except PlaywrightError as exc:
            if "existing browser session" in str(exc):
                raise RuntimeError(
                    "The Playwright profile is already open. Close every Chrome "
                    f"window using {profile_directory} before starting the MCP server."
                ) from exc

            raise RuntimeError(
                "Chrome could not be launched with the Playwright profile."
            ) from exc

        page = context.pages[0] if context.pages else context.new_page()

        yield context, page

    finally:
        if context is not None:
            try:
                context.close()
            except PlaywrightError:
                pass

        try:
            playwright.stop()
        except PlaywrightError:
            pass