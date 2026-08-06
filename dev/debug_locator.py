import sys
from pathlib import Path

PROJECT_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIRECTORY))

from auth import ensure_profile_directory
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(ensure_profile_directory()),
        channel="chrome",
        headless=False,
    )

    page = browser.new_page()

    page.goto(
        "https://app.kalvium.community/livebooks/2635/058d6e95-732c-4750-9fb9-e09e7ca14f6c/lessons",
        wait_until="load"
    )

    input("Wait until the lesson is fully visible, then press Enter...")

    input("Keep the browser open. Press Enter here only after you're done inspecting.")

    browser.close()
