from auth import ensure_profile_directory
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(ensure_profile_directory()),
        channel="chrome",
        headless=False,
    )

    print("1")

    page = browser.new_page()

    print("2")

    page.goto(
    "https://app.kalvium.community/dashboard",
    wait_until="domcontentloaded",
    timeout=30000,
)

    print("3")

    print(page.title())

    input("Press Enter...")

    browser.close()
